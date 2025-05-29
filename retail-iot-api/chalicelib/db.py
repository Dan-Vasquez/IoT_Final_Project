############################################################
# Módulo de Acceso a Base de Datos para IoT Retail API    #
# Proporciona funciones para interactuar con PostgreSQL     #
# y gestionar dispositivos IoT y sus eventos               #
############################################################

import os              # Para variables de entorno
import json            # Para serializar/deserializar datos JSON
import psycopg2        # Driver PostgreSQL
import psycopg2.extras # Extensiones para PostgreSQL (RealDictCursor)
from datetime import datetime  # Para manejo de fechas y horas
from dotenv import load_dotenv  # Para cargar variables de entorno desde .env

# Cargar variables de entorno para configuración de la base de datos
# Las variables se pueden definir en un archivo .env o en el entorno del sistema
load_dotenv()

# Configuración de la conexión a PostgreSQL
# Se utilizan valores predeterminados si no se encuentran las variables de entorno
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '34.227.160.239'),  # Servidor de base de datos
    'dbname': os.environ.get('DB_NAME', 'iot_final_project'),  # Nombre de la base de datos
    'user': os.environ.get('DB_USER', 'dok'),  # Usuario de la base de datos
    'password': os.environ.get('DB_PASSWORD', 'dok'),  # Contraseña
    'port': os.environ.get('DB_PORT', '5432')  # Puerto estándar PostgreSQL
}

def get_db_connection():
    """Establece y retorna una conexión a la base de datos PostgreSQL.
    
    Utiliza la configuración global DB_CONFIG para establecer la conexión.
    Si no se puede establecer la conexión, imprime un mensaje de error y
    relanza la excepción para que sea manejada por el código llamante.
    
    Returns:
        psycopg2.connection: Objeto de conexión a PostgreSQL activa
        
    Raises:
        Exception: Si ocurre un error al conectar a la base de datos
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise  # Relanzar la excepción para manejo superior

def get_all_sensors():
    """Obtiene todos los sensores registrados en la base de datos.
    
    Ejecuta una consulta para obtener todos los registros de la tabla 'sensors'.
    Para cada sensor, convierte los campos de fecha/hora a formato ISO 8601
    para facilitar la serialización a JSON en la API REST.
    
    Returns:
        list: Lista de diccionarios, cada uno representando un sensor con sus atributos:
              - sensor_id: ID único del sensor
              - name: Nombre descriptivo
              - type: Tipo de sensor (temperatura, humedad, etc.)
              - location: Ubicación física del sensor
              - status: Estado del sensor (active, inactive, etc.)
              - created_at: Fecha de creación en formato ISO 8601
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Usar RealDictCursor para obtener resultados como diccionarios
            cur.execute("SELECT * FROM sensors")
            sensors = cur.fetchall()
            
            # Convertir objetos datetime a strings en formato ISO 8601
            # para facilitar la serialización JSON
            for sensor in sensors:
                if sensor.get('created_at'):
                    sensor['created_at'] = sensor['created_at'].isoformat()
            return sensors
    finally:
        # Asegurar que la conexión se cierre siempre, incluso si ocurre una excepción
        conn.close()

def get_sensor_by_id(sensor_id):
    """Obtiene un sensor específico por su identificador único.
    
    Consulta la base de datos para encontrar un sensor que coincida con el ID proporcionado.
    Si no se encuentra ningún sensor con ese ID, devuelve None.
    
    Args:
        sensor_id (str): Identificador único del sensor a buscar
        
    Returns:
        dict or None: Diccionario con los datos del sensor si se encuentra, None en caso contrario.
                      El diccionario contiene los campos:
                      - sensor_id: ID único del sensor
                      - name: Nombre descriptivo
                      - type: Tipo de sensor
                      - location: Ubicación física
                      - status: Estado actual
                      - created_at: Fecha de creación
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Utilizamos parámetros para evitar inyección SQL
            cur.execute("SELECT * FROM sensors WHERE sensor_id = %s", (sensor_id,))
            # fetchone devuelve None si no hay resultados
            return cur.fetchone()
    finally:
        conn.close()

def create_sensor(sensor_id, name, type, location, status='active'):
    """Crea un nuevo sensor en la base de datos.
    
    Inserta un nuevo registro en la tabla 'sensors' con los datos proporcionados
    y devuelve el registro completo creado, incluyendo los campos generados automáticamente.
    
    Args:
        sensor_id (str): Identificador único para el sensor (ej: 'TEMP001')
        name (str): Nombre descriptivo del sensor (ej: 'Sensor de Temperatura Almacén')
        type (str): Tipo de sensor (ej: 'temperatura', 'humedad', 'movimiento')
        location (str): Ubicación física del sensor (ej: 'Almacén Principal')
        status (str, opcional): Estado inicial del sensor. Por defecto 'active'
        
    Returns:
        dict: Diccionario con todos los datos del sensor creado, incluyendo:
              - sensor_id: ID único asignado
              - name: Nombre descriptivo
              - type: Tipo de sensor
              - location: Ubicación física
              - status: Estado actual
              - created_at: Fecha y hora de creación en formato ISO 8601
              
    Raises:
        psycopg2.Error: Si ocurre un error durante la operación en la base de datos,
                        como violación de clave primaria (sensor_id duplicado)
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Usar timestamp actual para el campo created_at
            now = datetime.now()
            
            # Insertar el nuevo sensor y devolver todos los campos del registro creado
            cur.execute(
                """
                INSERT INTO sensors (sensor_id, name, type, location, created_at, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (sensor_id, name, type, location, now, status)
            )
            # Confirmar la transacción
            conn.commit()
            
            # Obtener el sensor creado
            sensor = cur.fetchone()

            # Convertir objeto datetime a string ISO 8601 para serialización JSON
            if sensor and sensor.get('created_at'):
                sensor['created_at'] = sensor['created_at'].isoformat()

            return sensor
    finally:
        # Cerrar la conexión incluso si ocurre una excepción
        conn.close()

def get_sensor_events(sensor_id, limit=100, start_date=None, end_date=None):
    """Obtiene los eventos históricos de un sensor específico con filtros opcionales.
    
    Consulta la tabla 'events' para obtener los eventos registrados por un sensor
    particular, con opciones para filtrar por rango de fechas y limitar la cantidad
    de resultados. Los eventos se ordenan del más reciente al más antiguo.
    
    Args:
        sensor_id (str): Identificador único del sensor
        limit (int, opcional): Número máximo de eventos a devolver. Por defecto 100
        start_date (str, opcional): Fecha de inicio para filtrar eventos (formato ISO 8601)
        end_date (str, opcional): Fecha de fin para filtrar eventos (formato ISO 8601)
        
    Returns:
        list: Lista de eventos del sensor, cada uno como un diccionario con los campos:
              - id: Identificador único del evento
              - device_id: ID del dispositivo que generó el evento
              - device_type: Tipo de dispositivo ('sensor' en este caso)
              - value: Valor registrado por el sensor
              - unit: Unidad de medida del valor
              - timestamp: Fecha y hora del evento en formato ISO 8601
              - metadata: Datos adicionales del evento (como JSON)
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Construir consulta SQL base
            query = """
                SELECT * FROM events 
                WHERE device_id = %s AND device_type = 'sensor'
            """
            params = [sensor_id]  # Parámetros para la consulta parametrizada

            # Añadir filtro de fecha de inicio si se proporciona
            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)

            # Añadir filtro de fecha de fin si se proporciona
            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)

            # Ordenar por timestamp descendente y limitar resultados
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)

            # Ejecutar la consulta con los parámetros
            cur.execute(query, params)
            events = cur.fetchall()

            # Convertir objetos datetime a strings ISO 8601 para serialización JSON
            for event in events:
                if event.get('timestamp'):
                    event['timestamp'] = event['timestamp'].isoformat()

            return events
    finally:
        conn.close()

def get_all_actuators():
    """Obtiene todos los actuadores registrados en la base de datos.
    
    Ejecuta una consulta para obtener todos los registros de la tabla 'actuators'.
    Para cada actuador, convierte los campos de fecha/hora a formato ISO 8601
    para facilitar la serialización a JSON en la API REST.
    
    Returns:
        list: Lista de diccionarios, cada uno representando un actuador con sus atributos:
              - actuator_id: ID único del actuador
              - name: Nombre descriptivo
              - type: Tipo de actuador (alarma, puerta, etc.)
              - location: Ubicación física del actuador
              - status: Estado del actuador (active, inactive, etc.)
              - created_at: Fecha de creación en formato ISO 8601
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Consultar todos los actuadores
            cur.execute("SELECT * FROM actuators")
            actuators = cur.fetchall()

            # Convertir objetos datetime a strings ISO 8601 para serialización JSON
            for actuator in actuators:
                if actuator.get('created_at'):
                    actuator['created_at'] = actuator['created_at'].isoformat()
            return actuators
    finally:
        # Asegurar cierre de conexión
        conn.close()

def create_actuator(actuator_id, name, type, location, status='active'):
    """Crea un nuevo actuador en la base de datos.
    
    Inserta un nuevo registro en la tabla 'actuators' con los datos proporcionados
    y devuelve el registro completo creado, incluyendo los campos generados automáticamente.
    
    Args:
        actuator_id (str): Identificador único para el actuador (ej: 'ALARM001')
        name (str): Nombre descriptivo del actuador (ej: 'Alarma Principal')
        type (str): Tipo de actuador (ej: 'alarma', 'puerta', 'luz')
        location (str): Ubicación física del actuador (ej: 'Entrada Principal')
        status (str, opcional): Estado inicial del actuador. Por defecto 'active'
        
    Returns:
        dict: Diccionario con todos los datos del actuador creado, incluyendo:
              - actuator_id: ID único asignado
              - name: Nombre descriptivo
              - type: Tipo de actuador
              - location: Ubicación física
              - status: Estado actual
              - created_at: Fecha y hora de creación en formato ISO 8601
              
    Raises:
        psycopg2.Error: Si ocurre un error durante la operación en la base de datos,
                        como violación de clave primaria (actuator_id duplicado)
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Usar timestamp actual para el campo created_at
            now = datetime.now()
            
            # Insertar el nuevo actuador y devolver todos los campos del registro creado
            cur.execute(
                """
                INSERT INTO actuators (actuator_id, name, type, location, created_at, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (actuator_id, name, type, location, now, status)
            )
            # Confirmar la transacción
            conn.commit()
            
            # Obtener el actuador creado
            actuator = cur.fetchone()

            # Convertir objeto datetime a string ISO 8601 para serialización JSON
            if actuator and actuator.get('created_at'):
                actuator['created_at'] = actuator['created_at'].isoformat()

            return actuator
    finally:
        # Cerrar la conexión incluso si ocurre una excepción
        conn.close()

def save_event(device_id, device_type, value, unit, timestamp=None, metadata=None):
    """Guarda un nuevo evento de dispositivo IoT en la base de datos.
    
    Registra un evento generado por un sensor o actuador en la tabla 'events'.
    El evento incluye un valor, su unidad de medida, timestamp y metadatos opcionales.
    
    Args:
        device_id (str): Identificador único del dispositivo que generó el evento
        device_type (str): Tipo de dispositivo ('sensor' o 'actuator')
        value (float/int/str): Valor registrado por el dispositivo
        unit (str): Unidad de medida del valor (ej: 'C', '%', 'estado')
        timestamp (datetime, opcional): Fecha y hora del evento. Si es None, se usa la hora actual
        metadata (dict, opcional): Datos adicionales sobre el evento en formato diccionario
        
    Returns:
        dict: Diccionario con todos los datos del evento guardado, incluyendo:
              - id: ID autogenerado para el evento
              - device_id: ID del dispositivo
              - device_type: Tipo del dispositivo
              - value: Valor registrado
              - unit: Unidad de medida
              - timestamp: Fecha y hora del evento en formato ISO 8601
              - metadata: Datos adicionales serializados
              
    Raises:
        psycopg2.Error: Si ocurre un error durante la inserción en la base de datos
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Usar timestamp actual si no se proporciona uno
            if timestamp is None:
                timestamp = datetime.now()

            # Inicializar metadata como diccionario vacío si es None
            if metadata is None:
                metadata = {}

            # Insertar el evento y devolver el registro completo
            cur.execute(
                """
                INSERT INTO events (device_id, device_type, value, unit, timestamp, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                # Serializar metadata a JSON para almacenamiento
                (device_id, device_type, value, unit, timestamp, json.dumps(metadata))
            )
            # Confirmar transacción
            conn.commit()
            event = cur.fetchone()

            # Convertir objeto datetime a string ISO 8601 para serialización JSON
            if event and event.get('timestamp'):
                event['timestamp'] = event['timestamp'].isoformat()

            return event
    finally:
        # Asegurar cierre de conexión
        conn.close()
