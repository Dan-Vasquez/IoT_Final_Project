# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

#######################################################
# Script de publicación MQTT para IoT Retail Project  #
# Publica mensajes MQTT para simular sensores y      #
# actuadores IoT en AWS IoT Core                     #
#######################################################

# Imports para funcionalidad MQTT y AWS IoT
from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
import sys
import threading
import time
import json
import argparse
from utils.command_line_utils import CommandLineUtils

# Este script permite publicar mensajes en AWS IoT Core a través de MQTT.
# Se utiliza para enviar datos de sensores y actuadores simulados al broker MQTT.
# El script puede recibir datos específicos de sensores (nombre, valor, unidad)
# como argumentos de línea de comandos, o usar valores predeterminados.

# ===== Configuración de la línea de comandos =====

# Primero, procesamos los argumentos estándar de conexión MQTT usando la utilidad de AWS
# Esto incluye argumentos como --endpoint, --cert, --key, --topic, etc.
cmdData = CommandLineUtils.parse_sample_input_pubsub()

# Agregamos argumentos personalizados para los datos de sensores/actuadores
parser = argparse.ArgumentParser(description="Publicador MQTT para datos de sensores y actuadores IoT")

# Argumentos específicos para datos de sensores/actuadores
parser.add_argument("--sensor_name", 
                    help="Nombre del sensor/actuador en formato tipo_ID (ej: movimiento_MOV001)")
parser.add_argument("--sensor_value", 
                    help="Valor numérico del sensor/actuador (ej: 1 para activo, 0 para inactivo)", 
                    type=float)
parser.add_argument("--sensor_unit", 
                    help="Unidad de medida del valor (ej: estado, grados, etc.)")
parser.add_argument("--additional_data", 
                    help="Datos adicionales en formato JSON (ej: '{\"area\":\"Almacén Principal\"}')")

# Procesamiento selectivo de argumentos
# Como ya procesamos algunos argumentos con CommandLineUtils, necesitamos
# filtrar sys.argv para procesar solo los argumentos personalizados
new_args = []
for arg in sys.argv[1:]:
    # Incluir argumentos que empiezan con --sensor o --additional_data
    if arg.startswith("--sensor") or arg.startswith("--additional_data"):
        new_args.append(arg)
    # Incluir argumentos en formato clave=valor si la clave es uno de nuestros argumentos personalizados
    elif "=" in arg and arg.split("=")[0].replace("--", "") in ["sensor_name", "sensor_value", "sensor_unit", "additional_data"]:
        new_args.append(arg)

# Parsear solo los argumentos personalizados
sensor_args = parser.parse_args(new_args)

received_count = 0
received_all_event = threading.Event()

# ===== Callbacks de gestión de conexiones MQTT =====

def on_connection_interrupted(connection, error, **kwargs):
    """Maneja los eventos de interrupción de la conexión MQTT.
    
    Esta función se llama cuando la conexión MQTT es interrumpida de forma inesperada,
    como puede ocurrir por problemas de red o timeout del servidor.
    
    Args:
        connection: Objeto de conexión MQTT
        error: Código de error que indica la razón de la interrupción
        **kwargs: Argumentos adicionales proporcionados por el cliente MQTT
    """
    print("Conexión interrumpida. error: {}".format(error))

def on_connection_resumed(connection, return_code, session_present, **kwargs):
    """Maneja los eventos de reanudación de una conexión MQTT interrumpida.
    
    Esta función se llama cuando la conexión MQTT se restablece después de una interrupción.
    Si la sesión no se ha mantenido en el servidor, vuelve a suscribirse a los tópicos anteriores.
    
    Args:
        connection: Objeto de conexión MQTT
        return_code: Código de retorno que indica el estado de la conexión restablecida
        session_present: Booleano que indica si la sesión anterior se ha mantenido
        **kwargs: Argumentos adicionales proporcionados por el cliente MQTT
    """
    print("Conexión reanudada. return_code: {} session_present: {}".format(return_code, session_present))

    # Si la conexión es aceptada pero la sesión no persistió, debemos volver a suscribirnos
    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Sesión did not persist. Resubscribing a tópicos existentes...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Señalamos cuando haya terminado de volver a subscribirse
        resubscribe_future.add_done_callback(on_resubscribe_complete)

def on_resubscribe_complete(resubscribe_future):
    """Procesa el resultado de la resuscripción a tópicos MQTT.
    
    Esta función se llama cuando el proceso de resuscripción a tópicos ha terminado,
    ya sea con éxito o con error.
    
    Args:
        resubscribe_future: Objeto Future que contiene los resultados de la resuscripción
    """
    # Obtener los resultados de la resuscripción
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))

    # Verificar si alguna suscripción fue rechazada por el servidor
    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))

def on_connection_success(connection, callback_data):
    """Maneja el evento de conexión MQTT exitosa.
    
    Esta función se llama cuando la conexión MQTT se establece con éxito.
    
    Args:
        connection: Objeto de conexión MQTT
        callback_data: Datos de retorno de la conexión exitosa
    """
    assert isinstance(callback_data, mqtt.OnConnectionSuccessData)
    print("Connection Successful with return code: {} session present: {}".format(callback_data.return_code, callback_data.session_present))

def on_connection_failure(connection, callback_data):
    """Maneja el evento de fallo en la conexión MQTT.
    
    Esta función se llama cuando no se puede establecer la conexión MQTT.
    
    Args:
        connection: Objeto de conexión MQTT
        callback_data: Datos con información sobre el error de conexión
    """
    assert isinstance(callback_data, mqtt.OnConnectionFailureData)
    print("Connection failed with error code: {}".format(callback_data.error))

def on_connection_closed(connection, callback_data):
    """Maneja el evento de cierre de la conexión MQTT.
    
    Esta función se llama cuando la conexión MQTT se cierra de forma normal o
    debido a un error.
    
    Args:
        connection: Objeto de conexión MQTT
        callback_data: Datos relacionados con el cierre de la conexión
    """
    print("Connection closed")

if __name__ == '__main__':
    # ===== Configuración y establecimiento de la conexión MQTT =====
    
    # Crear las opciones de proxy si se proporcionaron en la línea de comandos
    proxy_options = None
    if cmdData.input_proxy_host is not None and cmdData.input_proxy_port != 0:
        proxy_options = http.HttpProxyOptions(
            host_name=cmdData.input_proxy_host,
            port=cmdData.input_proxy_port)

    # Crear una conexión MQTT utilizando los certificados SSL/TLS mutuo (mTLS)
    # Los parámetros se obtienen de los argumentos de línea de comandos
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=cmdData.input_endpoint,      # Endpoint de AWS IoT
        port=cmdData.input_port,              # Puerto, generalmente 8883 para MQTT sobre TLS
        cert_filepath=cmdData.input_cert,     # Ruta al certificado del cliente
        pri_key_filepath=cmdData.input_key,   # Ruta a la clave privada del cliente
        ca_filepath=cmdData.input_ca,         # Ruta al certificado de la CA raíz de AWS
        
        # Callbacks para manejar eventos de conexión
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        
        # Parámetros de la sesión MQTT
        client_id=cmdData.input_clientId,     # ID único del cliente
        clean_session=False,                  # Mantener la sesión entre reconexiones
        keep_alive_secs=30,                   # Intervalo de keep-alive en segundos
        http_proxy_options=proxy_options,  # Configuración de proxy si existe
       
        # Callbacks para manejar eventos de conexión
        on_connection_success=on_connection_success,
        on_connection_failure=on_connection_failure,
        on_connection_closed=on_connection_closed)
        

    # Mostrar información sobre la conexión que se va a establecer
    if not cmdData.input_is_ci:
        print(f"Connecting to {cmdData.input_endpoint} with client ID '{cmdData.input_clientId}'...")
    else:
        print("Connecting to endpoint with client ID")
    
    # Iniciar el proceso de conexión de forma asíncrona
    connect_future = mqtt_connection.connect()

    # Esperar a que la conexión se complete (bloqueante)
    connect_future.result()
    print("Connected!")

    # ===== Preparación del mensaje a publicar =====
    
    # Obtener el número de mensajes a enviar y el tópico desde los argumentos
    message_count = cmdData.input_count
    message_topic = cmdData.input_topic

    # Determinar el contenido del mensaje a publicar
    if cmdData.input_message is not None and cmdData.input_message != "":
        # Usar el mensaje proporcionado directamente en la línea de comandos
        message_string = cmdData.input_message
    else:
        # Crear un mensaje JSON con los datos del sensor proporcionados
        data = {
            # Usar valores proporcionados por línea de comandos o valores por defecto
            "sensor": sensor_args.sensor_name if hasattr(sensor_args, 'sensor_name') else "temperatura",
            "value": sensor_args.sensor_value if hasattr(sensor_args, 'sensor_value') else 25.0,
            "unit": sensor_args.sensor_unit if hasattr(sensor_args, 'sensor_unit') else "C",
            # Agregar timestamp en formato ISO 8601
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        # Incorporar datos adicionales al mensaje si fueron proporcionados
        try:
            if hasattr(sensor_args, 'additional_data') and sensor_args.additional_data:
                # Parsear el JSON adicional y agregarlo al mensaje
                additional_data = json.loads(sensor_args.additional_data)
                data.update(additional_data)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse additional_data: {sensor_args.additional_data}")
        
        # Convertir el diccionario a una cadena JSON
        message_string = json.dumps(data)

    # ===== Publicación de mensajes MQTT =====
    
    # La funcionalidad de suscripción está comentada ya que este script está diseñado
    # principalmente para publicar mensajes, no para recibir respuestas
    '''
    print("Subscribing to topic '{}'...".format(message_topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=message_topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result['qos'])))
    '''
    
    # Publicar el mensaje al broker MQTT el número de veces especificado
    # Solo se ejecuta si el mensaje no está vacío
    # Si message_count es 0, se envía indefinidamente hasta detener el programa
    if message_string:
        # Informar sobre el modo de envío (cantidad fija o continuo)
        if message_count == 0:
            print("Sending messages until program killed")
        else:
            print("Sending {} message(s)".format(message_count))

        # Iniciar contador de publicaciones
        publish_count = 1
        
        # Bucle de publicación de mensajes
        while (publish_count <= message_count) or (message_count == 0):
            # Formatear mensaje con contador para seguimiento
            message = "{} [{}]".format(message_string, publish_count)
            print("Publishing message to topic '{}': {}".format(message_topic, message))
            
            # Publicar mensaje al broker MQTT
            mqtt_connection.publish(
                topic=message_topic,          # Tópico MQTT destino
                payload=message_string,       # Contenido del mensaje (JSON)
                qos=mqtt.QoS.AT_LEAST_ONCE)   # Calidad de servicio (QoS 1)
                
            # Esperar un segundo entre publicaciones
            time.sleep(1)
            publish_count += 1

    # El código para esperar mensajes de respuesta está comentado
    # ya que este script se enfoca en la publicación de mensajes
    """
    if message_count != 0 and not received_all_event.is_set():
        print("Waiting for all messages to be received...")

        received_all_event.wait()
        print("{} message(s) received.".format(received_count))
    """
    
    # Desconectar la conexión MQTT
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")
