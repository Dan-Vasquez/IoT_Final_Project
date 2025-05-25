"""
Script de prueba para verificar la publicación de un sensor en AWS IoT Core.
Este script ejecuta un solo ciclo de un sensor y verifica que los datos se envíen correctamente.
"""

import time
import sys
from sensor_movimiento import SensorMovimiento
from sensor_apertura import SensorApertura
from etiqueta_rfid import EtiquetaRFID
from actuador_alarma import ActuadorAlarma
from actuador_puerta import ActuadorPuertaAutomatica

def test_sensor_movimiento():
    print("\n=== PRUEBA DE SENSOR DE MOVIMIENTO ===")
    sensor = SensorMovimiento("MOV_TEST", "Área de Prueba")
    # Forzar un estado para la prueba
    sensor.movimiento_detectado = True
    print(sensor.obtener_estado_str())
    
    # Publicar en AWS IoT
    exito = sensor.publicar_en_aws_iot()
    if exito:
        print("✅ Publicación exitosa en AWS IoT")
    else:
        print("❌ Error al publicar en AWS IoT")
    return exito

def test_sensor_apertura():
    print("\n=== PRUEBA DE SENSOR DE APERTURA ===")
    sensor = SensorApertura("APE_TEST", "Puerta de Prueba")
    # Forzar un estado para la prueba
    sensor.abierto = True
    print(sensor.obtener_estado_str())
    
    # Publicar en AWS IoT
    exito = sensor.publicar_en_aws_iot()
    if exito:
        print("✅ Publicación exitosa en AWS IoT")
    else:
        print("❌ Error al publicar en AWS IoT")
    return exito

def test_etiqueta_rfid():
    print("\n=== PRUEBA DE ETIQUETA RFID ===")
    etiqueta = EtiquetaRFID("RFID_TEST", "Producto de Prueba")
    # Forzar un estado para la prueba
    etiqueta.alarma_activa = True
    print(etiqueta.obtener_estado_str())
    
    # Publicar en AWS IoT
    exito = etiqueta.publicar_en_aws_iot()
    if exito:
        print("✅ Publicación exitosa en AWS IoT")
    else:
        print("❌ Error al publicar en AWS IoT")
    return exito

def test_actuador_alarma():
    print("\n=== PRUEBA DE ACTUADOR DE ALARMA ===")
    alarma = ActuadorAlarma("ALM_TEST", ubicacion="Ubicación de Prueba")
    # Forzar un estado para la prueba
    alarma.activar()
    print(alarma.obtener_estado_str())
    
    # Publicar en AWS IoT
    exito = alarma.publicar_en_aws_iot()
    if exito:
        print("✅ Publicación exitosa en AWS IoT")
    else:
        print("❌ Error al publicar en AWS IoT")
    return exito

def test_actuador_puerta():
    print("\n=== PRUEBA DE ACTUADOR DE PUERTA ===")
    puerta = ActuadorPuertaAutomatica("PTA_TEST", "Ubicación de Prueba")
    # Forzar un estado para la prueba
    puerta.abrir()
    print(puerta.obtener_estado_str())
    
    # Publicar en AWS IoT
    exito = puerta.publicar_en_aws_iot()
    if exito:
        print("✅ Publicación exitosa en AWS IoT")
    else:
        print("❌ Error al publicar en AWS IoT")
    return exito

if __name__ == "__main__":
    print("=== INICIANDO PRUEBAS DE SENSORES Y ACTUADORES ===")
    print("Este script probará la publicación de datos en AWS IoT Core")
    
    # Determinar qué probar según el argumento
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    else:
        test_type = "all"
    
    results = []
    
    # Ejecutar pruebas según lo solicitado
    if test_type == "all" or test_type == "movimiento":
        results.append(("Sensor de Movimiento", test_sensor_movimiento()))
    
    if test_type == "all" or test_type == "apertura":
        results.append(("Sensor de Apertura", test_sensor_apertura()))
    
    if test_type == "all" or test_type == "rfid":
        results.append(("Etiqueta RFID", test_etiqueta_rfid()))
    
    if test_type == "all" or test_type == "alarma":
        results.append(("Actuador de Alarma", test_actuador_alarma()))
    
    if test_type == "all" or test_type == "puerta":
        results.append(("Actuador de Puerta", test_actuador_puerta()))
    
    # Resumen de resultados
    print("\n=== RESUMEN DE PRUEBAS ===")
    all_success = True
    for name, success in results:
        status = "✅ EXITOSO" if success else "❌ FALLIDO"
        print(f"{name}: {status}")
        all_success = all_success and success
    
    print("\nTodas las pruebas " + ("exitosas ✅" if all_success else "fallidas ❌"))
    print("Para ver los mensajes publicados, use el suscriptor MQTT de AWS IoT Core")
