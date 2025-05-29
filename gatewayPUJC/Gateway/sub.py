# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
import sys
import threading
import time
import json
from utils.command_line_utils import CommandLineUtils

# Agregar estos imports al inicio del archivo
import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno para configuración de la base de datos
load_dotenv()

# Configuración de la conexión a PostgreSQL
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '34.227.160.239'),
    'dbname': os.environ.get('DB_NAME', 'iot_final_project'),
    'user': os.environ.get('DB_USER', 'dok'),
    'password': os.environ.get('DB_PASSWORD', 'dok'),
    'port': os.environ.get('DB_PORT', '5432')
}

# Mapeo de sensores por tipo (puedes ampliarlo según tus sensores)
SENSOR_TYPE_MAP = {
    # Sensores de movimiento
    'MOV': 'movimiento',
    # Sensores de apertura
    'APR': 'apertura',
    # Etiquetas RFID
    'RFID': 'rfid',
}

# Mapeo de actuadores por tipo
ACTUATOR_TYPE_MAP = {
    # Actuadores de alarma
    'ALM': 'alarma',
    # Actuadores de puerta
    'PTA': 'puerta',
}

def get_db_connection():
    """Establece y retorna una conexión a la base de datos PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise

def save_event(device_id, device_type, value, unit, timestamp=None, metadata=None):
    """Guarda un nuevo evento en la base de datos"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if timestamp is None:
                timestamp = datetime.now()
                
            if metadata is None:
                metadata = {}
                
            cur.execute(
                """
                INSERT INTO events (device_id, device_type, value, unit, timestamp, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (device_id, device_type, value, unit, timestamp, json.dumps(metadata))
            )
            conn.commit()
            event = cur.fetchone()
            # Convertir objeto datetime a string para mostrar en consola
            if event and event.get('timestamp'):
                event['timestamp'] = event['timestamp'].isoformat()
            return event
    except Exception as e:
        print(f"Error al guardar evento: {e}")
        return None
    finally:
        conn.close()

def determine_device_type_from_topic(topic):
    """Determina el tipo de dispositivo y su ID basado en el tópico MQTT"""
    # Formato esperado: data/retail/sensors/{tipo_sensor}/{id_sensor}
    # o data/retail/actuadores/{tipo_actuador}/{id_actuador}
    parts = topic.split('/')
    if len(parts) >= 5:
        category = parts[2]  # 'sensors' o 'actuadores'
        device_type = parts[3]  # 'movimiento', 'apertura', 'rfid', 'alarma', 'puerta'
        device_id = parts[4]  # ID del dispositivo
        
        return {
            'category': category,
            'device_type': device_type,
            'device_id': device_id
        }
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
    try:
        print(f"\nRecibido mensaje del tópico '{topic}'")
        
        # Parsear el payload como JSON
        try:
            payload_text = payload.decode('utf-8')
            message = json.loads(payload_text)
            print(f"Contenido del mensaje: {json.dumps(message, indent=2)}")
        except json.JSONDecodeError:
            print(f"Error: No se pudo decodificar el mensaje JSON: {payload_text}")
            return
        except Exception as e:
            print(f"Error al procesar el mensaje: {e}")
            return
        
        # Extraer información del tópico
        topic_info = determine_device_type_from_topic(topic)
        if not topic_info:
            print("Error: No se pudo determinar el tipo de dispositivo del tópico")
            return
        
        # Extraer información relevante del mensaje
        device_id = topic_info['device_id']
        
        # Determinar si es un sensor o actuador
        is_actuator = topic_info['category'] == 'actuadores'
        device_type = 'actuator' if is_actuator else 'sensor'
        
        # Extraer otros campos del mensaje
        # Asegúrate de que value sea un número
        value = float(message.get('value', 0))
        unit = message.get('unit', '')
        timestamp_str = message.get('timestamp')
        
        # Convertir timestamp si existe
        timestamp = None
        if timestamp_str:
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                print(f"Error: Formato de timestamp inválido: {timestamp_str}")
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        # Construir metadata con campos adicionales
        metadata = {}
        for key, val in message.items():
            if key not in ['sensor', 'value', 'unit', 'timestamp']:
                metadata[key] = val
        
        # Guardar el evento en la base de datos
        print(f"Guardando evento para {device_type} {device_id}...")
        event = save_event(
            device_id=device_id,
            device_type=device_type,
            value=value,
            unit=unit,
            timestamp=timestamp,
            metadata=metadata
        )
        
        if event:
            print(f"Evento guardado exitosamente: {json.dumps(event, indent=2)}")
        else:
            print("Error: No se pudo guardar el evento")
        
        # Incrementar contador global de mensajes recibidos
        global received_count
        received_count += 1
        if received_count == cmdData.input_count:
            received_all_event.set()
    
    except Exception as e:
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