# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

#######################################################
# Script de suscripción MQTT para IoT Retail Project  #
# Recibe mensajes de sensores y actuadores y los     #
# almacena en la base de datos PostgreSQL            #
#######################################################

# Imports para funcionalidad MQTT y AWS IoT
from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
import sys
import threading
import time
import json
from utils.command_line_utils import CommandLineUtils

# Imports para manejo de base de datos PostgreSQL
import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno para configuración de la base de datos
load_dotenv()

# Configuración de la conexión a PostgreSQL
# Se obtienen los valores de variables de entorno, con valores por defecto en caso de no encontrarlos
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '34.227.160.239'),      # Dirección IP o hostname del servidor PostgreSQL
    'dbname': os.environ.get('DB_NAME', 'iot_final_project'),  # Nombre de la base de datos
    'user': os.environ.get('DB_USER', 'dok'),                  # Usuario de la base de datos
    'password': os.environ.get('DB_PASSWORD', 'dok'),          # Contraseña del usuario
    'port': os.environ.get('DB_PORT', '5432')                  # Puerto de PostgreSQL (estándar: 5432)
}

# Mapeo de prefijos de IDs de sensores a tipos de sensores
# Permite identificar el tipo de sensor basado en el prefijo de su ID
SENSOR_TYPE_MAP = {
    'MOV': 'movimiento',  # Prefijo MOV corresponde a sensores de movimiento
    'APR': 'apertura',    # Prefijo APR corresponde a sensores de apertura
    'RFID': 'rfid',       # Prefijo RFID corresponde a etiquetas RFID
}

# Mapeo de prefijos de IDs de actuadores a tipos de actuadores
# Permite identificar el tipo de actuador basado en el prefijo de su ID
ACTUATOR_TYPE_MAP = {
    'ALM': 'alarma',      # Prefijo ALM corresponde a actuadores de alarma
    'PTA': 'puerta',      # Prefijo PTA corresponde a actuadores de puerta
}

def get_db_connection():
    """Establece y retorna una conexión a la base de datos PostgreSQL.
    
    Utiliza la configuración en DB_CONFIG para establecer la conexión.
    
    Returns:
        connection: Objeto de conexión a PostgreSQL
        
    Raises:
        Exception: Si no se puede establecer la conexión a la base de datos
    """
    try:
        # Crear conexión usando los parámetros de configuración
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise

def save_event(device_id, device_type, value, unit, timestamp=None, metadata=None):
    """Guarda un nuevo evento en la base de datos PostgreSQL.
    
    Almacena los datos de un evento generado por un sensor o actuador en la tabla 'events'.
    
    Args:
        device_id (str): Identificador único del dispositivo (sensor o actuador)
        device_type (str): Tipo de dispositivo ('sensor' o 'actuator')
        value (float): Valor registrado por el dispositivo
        unit (str): Unidad de medida del valor
        timestamp (datetime, optional): Marca de tiempo del evento. Si es None, se usa la hora actual.
        metadata (dict, optional): Datos adicionales del evento en formato diccionario. Si es None, se usa un diccionario vacío.
    
    Returns:
        dict: Datos del evento guardado, con timestamps convertidos a formato ISO 8601, o None si ocurre un error
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Usar la hora actual si no se proporciona timestamp
            if timestamp is None:
                timestamp = datetime.now()
                
            # Usar diccionario vacío si no se proporcionan metadatos
            if metadata is None:
                metadata = {}
                
            # Insertar el evento en la tabla events
            cur.execute(
                """
                INSERT INTO events (device_id, device_type, value, unit, timestamp, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (device_id, device_type, value, unit, timestamp, json.dumps(metadata))
            )
            conn.commit()
            
            # Obtener el evento insertado
            event = cur.fetchone()
            
            # Convertir objeto datetime a string para mostrar en consola
            if event and event.get('timestamp'):
                event['timestamp'] = event['timestamp'].isoformat()
            return event
    except Exception as e:
        print(f"Error al guardar evento: {e}")
        return None
    finally:
        # Asegurar que la conexión se cierre incluso si ocurre una excepción
        conn.close()

def determine_device_type_from_topic(topic):
    """Determina el tipo de dispositivo y su ID basado en el tópico MQTT.
    
    Analiza la estructura del tópico MQTT para extraer información sobre el tipo de dispositivo
    y su identificador. La estructura esperada del tópico es:
    data/retail/sensors/{tipo_sensor}/{id_sensor} para sensores
    data/retail/actuadores/{tipo_actuador}/{id_actuador} para actuadores
    
    Args:
        topic (str): Tópico MQTT completo del mensaje recibido
        
    Returns:
        dict: Diccionario con las claves 'category', 'device_type', y 'device_id' si el tópico tiene
              un formato válido, o None si el formato es inválido
              - category: 'sensors' o 'actuadores'
              - device_type: tipo específico ('movimiento', 'apertura', 'rfid', 'alarma', 'puerta')
              - device_id: identificador único del dispositivo
    """
    # Dividir el tópico por '/' para analizar sus componentes
    parts = topic.split('/')
    
    # Verificar que el tópico tiene suficientes partes
    if len(parts) >= 5:
        # Extraer información relevante
        category = parts[2]    # 'sensors' o 'actuadores'
        device_type = parts[3] # tipo de sensor/actuador
        device_id = parts[4]   # ID del dispositivo
        
        # Devolver la información en un diccionario
        return {
            'category': category,
            'device_type': device_type,
            'device_id': device_id
        }
    # Si el tópico no tiene el formato esperado, devolver None
    return None


# This sample uses the Message Broker for AWS IoT to send and receive messages
# through an MQTT connection. On startup, the device connects to the server,
# subscribes to a topic, and begins publishing messages to that topic.
# The device should receive those same messages back from the message broker,
# since it is subscribed to that same topic.

# cmdData is the arguments/input from the command line placed into a single struct for
# use in this sample. This handles all of the command line parsing, validating, etc.
# See the Utils/CommandLineUtils for more information.
cmdData = CommandLineUtils.parse_sample_input_pubsub()

received_count = 0
received_all_event = threading.Event()

# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))


# Callback when the subscribed topic receives a message - Modificado
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    """Manejador de mensajes MQTT recibidos con almacenamiento en base de datos.
    
    Esta función es llamada automáticamente cuando se recibe un mensaje en un tópico al que
    el cliente está suscrito. Procesa el mensaje JSON, extrae la información relevante y
    guarda los datos del evento en la base de datos PostgreSQL.
    
    Args:
        topic (str): Tópico MQTT del mensaje recibido
        payload (bytes): Contenido del mensaje en formato bytes
        dup (bool): Indicador de mensaje duplicado
        qos (int): Nivel de calidad de servicio (0, 1 o 2)
        retain (bool): Indicador de mensaje retenido
        **kwargs: Argumentos adicionales proporcionados por el cliente MQTT
        
    No devuelve ningún valor, pero incrementa el contador global de mensajes recibidos
    y muestra información en la consola sobre el procesamiento del mensaje.
    """
    try:
        print(f"\nRecibido mensaje del tópico '{topic}'")
        
        # Paso 1: Decodificar y parsear el payload JSON
        try:
            # Convertir bytes a texto UTF-8
            payload_text = payload.decode('utf-8')
            # Parsear el texto como JSON
            message = json.loads(payload_text)
            print(f"Contenido del mensaje: {json.dumps(message, indent=2)}")
        except json.JSONDecodeError:
            print(f"Error: No se pudo decodificar el mensaje JSON: {payload_text}")
            return
        except Exception as e:
            print(f"Error al procesar el mensaje: {e}")
            return
        
        # Paso 2: Extraer información del tópico MQTT
        topic_info = determine_device_type_from_topic(topic)
        if not topic_info:
            print("Error: No se pudo determinar el tipo de dispositivo del tópico")
            return
        
        # Paso 3: Extraer y procesar la información del dispositivo
        device_id = topic_info['device_id']
        
        # Determinar si es un sensor o actuador basándose en la categoría del tópico
        is_actuator = topic_info['category'] == 'actuadores'
        device_type = 'actuator' if is_actuator else 'sensor'
        
        # Paso 4: Extraer y validar los campos del mensaje
        # Convertir el valor a número flotante (importante para la base de datos)
        value = float(message.get('value', 0))
        unit = message.get('unit', '')
        timestamp_str = message.get('timestamp')
        
        # Paso 5: Procesar el timestamp
        timestamp = None
        if timestamp_str:
            try:
                # Intentar parsear el timestamp en formato ISO 8601
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                print(f"Error: Formato de timestamp inválido: {timestamp_str}")
                timestamp = datetime.now()
        else:
            # Si no hay timestamp, usar la hora actual
            timestamp = datetime.now()
        
        # Paso 6: Construir metadata con campos adicionales
        # Cualquier campo que no sea estándar se guarda como metadata
        metadata = {}
        for key, val in message.items():
            if key not in ['sensor', 'value', 'unit', 'timestamp']:
                metadata[key] = val
        
        # Paso 7: Guardar el evento en la base de datos
        print(f"Guardando evento para {device_type} {device_id}...")
        event = save_event(
            device_id=device_id,
            device_type=device_type,
            value=value,
            unit=unit,
            timestamp=timestamp,
            metadata=metadata
        )
        
        # Paso 8: Informar sobre el resultado de la operación
        if event:
            print(f"Evento guardado exitosamente: {json.dumps(event, indent=2)}")
        else:
            print("Error: No se pudo guardar el evento")
        
        # Paso 9: Actualizar contador de mensajes y señalizar eventos
        global received_count
        received_count += 1
        # Si se ha alcanzado el número esperado de mensajes, señalizar el evento
        if received_count == cmdData.input_count:
            received_all_event.set()
    
    except Exception as e:
        # Capturar cualquier excepción no manejada para evitar interrupciones
        print(f"Error general en on_message_received: {e}")

# Callback when the connection successfully connects
def on_connection_success(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionSuccessData)
    print("Connection Successful with return code: {} session present: {}".format(callback_data.return_code, callback_data.session_present))

# Callback when a connection attempt fails
def on_connection_failure(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionFailureData)
    print("Connection failed with error code: {}".format(callback_data.error))

# Callback when a connection has been disconnected or shutdown successfully
def on_connection_closed(connection, callback_data):
    print("Connection closed")

if __name__ == '__main__':
    # Create the proxy options if the data is present in cmdData
    proxy_options = None
    if cmdData.input_proxy_host is not None and cmdData.input_proxy_port != 0:
        proxy_options = http.HttpProxyOptions(
            host_name=cmdData.input_proxy_host,
            port=cmdData.input_proxy_port)

    # Create a MQTT connection from the command line data
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=cmdData.input_endpoint,
        port=cmdData.input_port,
        cert_filepath=cmdData.input_cert,
        pri_key_filepath=cmdData.input_key,
        ca_filepath=cmdData.input_ca,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=cmdData.input_clientId,
        clean_session=False,
        keep_alive_secs=30,
        http_proxy_options=proxy_options,
        on_connection_success=on_connection_success,
        on_connection_failure=on_connection_failure,
        on_connection_closed=on_connection_closed)

    if not cmdData.input_is_ci:
        print(f"Connecting to {cmdData.input_endpoint} with client ID '{cmdData.input_clientId}'...")
    else:
        print("Connecting to endpoint with client ID")
    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    message_count = cmdData.input_count
    message_topic = cmdData.input_topic
    message_string = cmdData.input_message

    # Subscribe
    print("Subscribing to topic '{}'...".format(message_topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=message_topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result['qos'])))

    # Publish message to server desired number of times.
    # This step is skipped if message is blank.
    # This step loops forever if count was set to 0.
    """
    if message_string:
        if message_count == 0:
            print("Sending messages until program killed")
        else:
            print("Sending {} message(s)".format(message_count))

        publish_count = 1
        while (publish_count <= message_count) or (message_count == 0):
            message = "{} [{}]".format(message_string, publish_count)
            print("Publishing message to topic '{}': {}".format(message_topic, message))
            message_json = json.dumps(message)
            mqtt_connection.publish(
                topic=message_topic,
                payload=message_json,
                qos=mqtt.QoS.AT_LEAST_ONCE)
            time.sleep(1)
            publish_count += 1
    """
    # Wait for all messages to be received.
    # This waits forever if count was set to 0.
    if message_count != 0 and not received_all_event.is_set():
        print("Waiting for all messages to be received...")

    received_all_event.wait()
    print("{} message(s) received.".format(received_count))

    # Disconnect
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")