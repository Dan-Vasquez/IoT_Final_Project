############################################################
# API REST de IoT Retail para gestión de sensores y actuadores #
# Implementada con AWS Chalice para despliegue en AWS Lambda   #
############################################################

from chalice import Chalice, Response, BadRequestError, NotFoundError
from chalicelib.db import (
    get_all_sensors,   # Consultar todos los sensores registrados
    get_sensor_by_id,  # Obtener sensor por ID
    create_sensor,     # Registrar nuevo sensor
    get_sensor_events, # Obtener eventos de un sensor específico
    get_all_actuators, # Consultar todos los actuadores
    create_actuator    # Registrar nuevo actuador
)
import os              # Para manejo de variables de entorno
import json            # Para serialización/deserialización JSON
from datetime import datetime # Para manejo de fechas y horas

class DateTimeEncoder(json.JSONEncoder):
    """Codificador JSON personalizado para manejar objetos datetime.
    
    Esta clase extiende el codificador JSON estándar para convertir automáticamente
    objetos datetime en cadenas de texto ISO 8601, que son compatibles con JSON.
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # Convertir datetime a string formato ISO 8601
        return super().default(obj)  # Delegar a la implementación predeterminada para otros tipos

# =======================================================
# Configuración de la aplicación Chalice
# =======================================================

app = Chalice(app_name='retail-iot-api')     # Crear la aplicación Chalice con su nombre
app.api.binary_types.append('application/json')  # Configurar tipo de contenido binario para respuestas JSON
app.debug = True                             # Habilitar modo de depuración (desactivar en producción)
app.json_encoder = DateTimeEncoder           # Usar codificador personalizado para objetos datetime

# =======================================================
# Endpoints API para sensores
# =======================================================

@app.route('/sensors', methods=['GET'])
def list_sensors():
    """Endpoint para listar todos los sensores registrados.
    
    Returns:
        dict: Diccionario con la lista de sensores en formato JSON.
              Cada sensor incluye id, nombre, tipo, ubicación y estado.
    """
    sensors = get_all_sensors()  # Consulta a la base de datos
    return {'sensors': sensors}  # Devolver como respuesta JSON

@app.route('/sensors', methods=['POST'])
def add_sensor():
    """Endpoint para registrar un nuevo sensor en el sistema.
    
    Recibe un objeto JSON con los datos del sensor y lo guarda en la base de datos.
    Requiere campos obligatorios: sensor_id, name, type, location.
    El campo status es opcional y por defecto es 'active'.
    
    Returns:
        dict: Mensaje de éxito y datos del sensor creado
        
    Raises:
        BadRequestError: Si faltan campos requeridos o hay algún error en la creación
    """
    # Obtener el cuerpo de la solicitud como JSON
    body = app.current_request.json_body
    required_fields = ['sensor_id', 'name', 'type', 'location']
    
    # Verificar que todos los campos obligatorios estén presentes
    for field in required_fields:
        if field not in body:
            raise BadRequestError(f"Campo requerido '{field}' faltante")
    
    try:
        # Intentar crear el sensor en la base de datos
        sensor = create_sensor(
            sensor_id=body['sensor_id'],    # ID único del sensor
            name=body['name'],              # Nombre descriptivo 
            type=body['type'],              # Tipo (temperatura, humedad, etc.)
            location=body['location'],      # Ubicación física
            status=body.get('status', 'active')  # Estado (por defecto activo)
        )
        return {'message': 'Sensor creado exitosamente', 'sensor': sensor}
    except Exception as e:
        # Capturar cualquier excepción y registrar detalles para depuración
        import traceback
        error_details = traceback.format_exc()
        print(f"Error detallado: {error_details}")
        # Devolver error 400 con mensaje descriptivo
        raise BadRequestError(f"Error al crear sensor: {str(e)}")

@app.route('/sensors/{sensor_id}/events', methods=['GET'])
def get_events_for_sensor(sensor_id):
    """Endpoint para obtener el historial de eventos de un sensor específico.
    
    Permite consultar todos los eventos registrados por un sensor, con opciones
    de filtrado por fecha y limitación de resultados. Verifica primero que el 
    sensor exista en la base de datos.
    
    Args:
        sensor_id (str): Identificador único del sensor a consultar
        
    Query Parameters:
        limit (int, opcional): Número máximo de eventos a devolver (default: 100)
        start_date (str, opcional): Fecha de inicio para filtrar eventos (formato ISO)
        end_date (str, opcional): Fecha de fin para filtrar eventos (formato ISO)
    
    Returns:
        dict: Objeto JSON con el ID del sensor y la lista de eventos encontrados
        
    Raises:
        NotFoundError: Si el sensor especificado no existe en la base de datos
    """
    # Verificar que el sensor existe en la base de datos
    sensor = get_sensor_by_id(sensor_id)
    if not sensor:
        raise NotFoundError(f"Sensor con ID '{sensor_id}' no encontrado")
    
    # Extraer y procesar parámetros de consulta opcionales para filtrado
    params = app.current_request.query_params or {}
    limit = int(params.get('limit', 100))  # Límite de resultados (default: 100)
    start_date = params.get('start_date')   # Fecha inicio (opcional)
    end_date = params.get('end_date')       # Fecha fin (opcional)
    
    # Consultar eventos en la base de datos con los filtros aplicados
    events = get_sensor_events(
        sensor_id=sensor_id,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )
    
    # Devolver resultado como objeto JSON
    return {'sensor_id': sensor_id, 'events': events}

# =======================================================
# Endpoints API para actuadores
# =======================================================

@app.route('/actuators', methods=['GET'])
def list_actuators():
    """Endpoint para listar todos los actuadores registrados en el sistema.
    
    Devuelve una lista de todos los actuadores disponibles con sus detalles
    como ID, nombre, tipo, ubicación y estado actual.
    
    Returns:
        dict: Diccionario con la lista de actuadores en formato JSON.
              Cada actuador incluye id, nombre, tipo, ubicación y estado.
    """
    actuators = get_all_actuators()  # Consulta a la base de datos
    return {'actuators': actuators}  # Devolver como respuesta JSON

@app.route('/actuators', methods=['POST'])
def add_actuator():
    """Endpoint para registrar un nuevo actuador en el sistema.
    
    Recibe un objeto JSON con los datos del actuador y lo guarda en la base de datos.
    Requiere campos obligatorios: actuator_id, name, type, location.
    El campo status es opcional y por defecto es 'active'.
    
    Returns:
        dict: Mensaje de éxito y datos del actuador creado
        
    Raises:
        BadRequestError: Si faltan campos requeridos o hay algún error en la creación
    """
    # Obtener el cuerpo de la solicitud como JSON
    body = app.current_request.json_body
    required_fields = ['actuator_id', 'name', 'type', 'location']
    
    # Verificar que todos los campos obligatorios estén presentes
    for field in required_fields:
        if field not in body:
            raise BadRequestError(f"Campo requerido '{field}' faltante")
    
    try:
        # Intentar crear el actuador en la base de datos
        actuator = create_actuator(
            actuator_id=body['actuator_id'],  # ID único del actuador
            name=body['name'],                # Nombre descriptivo
            type=body['type'],                # Tipo (alarma, puerta, etc.)
            location=body['location'],        # Ubicación física
            status=body.get('status', 'active')  # Estado (por defecto activo)
        )
        return {'message': 'Actuador creado exitosamente', 'actuator': actuator}
    except Exception as e:
        # Devolver error 400 con mensaje descriptivo
        raise BadRequestError(f"Error al crear actuador: {str(e)}")

# =======================================================
# Endpoint de monitoreo y salud del servicio
# =======================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar el estado de salud de la API.
    
    Este endpoint sirve para monitoreo y alertas. Es utilizado por servicios
    de supervisión para verificar que la API está funcionando correctamente.
    
    Returns:
        dict: Estado de salud del servicio {'status': 'healthy'}
    """
    return {'status': 'healthy'}
