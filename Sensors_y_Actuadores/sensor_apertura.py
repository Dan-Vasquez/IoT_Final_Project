############################################################
# Simulador de Sensor de Apertura para Sistema IoT Retail  #
# Simula un sensor que detecta aperturas de puertas/ventanas#
# y publica eventos en AWS IoT Core                        #
############################################################

import random  # Para simulación de eventos aleatorios
import time    # Para timestamping y sleep
import subprocess  # Para ejecutar el script de publicación MQTT
import os     # Para manejo de rutas de archivos
import json   # Para formateo de mensajes JSON

class SensorApertura:
    """Clase que simula un sensor de apertura para puertas o ventanas en un entorno retail.
    
    Esta clase simula el comportamiento de un sensor magnético que detecta cuando una puerta
    o ventana se abre o cierra. El sensor puede enviar alertas cuando detecta una apertura
    y publicar su estado en AWS IoT Core para seguimiento en tiempo real.
    """
    
    def __init__(self, id_sensor, ubicacion="Puerta Desconocida"):
        """Inicializa un nuevo sensor de apertura.
        
        Args:
            id_sensor (str): Identificador único del sensor (ej: 'APR001')
            ubicacion (str): Ubicación física donde está instalado el sensor (por defecto: 'Puerta Desconocida')
        """
        self.id_sensor = id_sensor
        self.ubicacion = ubicacion
        self.abierto = False  # Estado inicial: puerta/ventana cerrada
        print(f"Sensor de Apertura [{self.id_sensor}] inicializado para: {self.ubicacion}")

    def simular_lectura(self):
        """Simula una lectura del sensor con probabilidades aleatorias de apertura/cierre.
        
        Este método simula el comportamiento normal de un sensor de apertura en un entorno real.
        Existe una baja probabilidad (5%) de que una puerta cerrada se abra (simulando una entrada).
        Existe una alta probabilidad (60%) de que una puerta abierta se cierre (simulando que alguien
        cierra la puerta después de entrar).
        
        Returns:
            bool: El estado actual del sensor después de la simulación (True=abierto, False=cerrado).
        """
        if not self.abierto and random.random() < 0.05:  # 5% de probabilidad de abrirse si está cerrado
            self.abierto = True
        elif self.abierto and random.random() < 0.6:    # 60% de probabilidad de cerrarse si estaba abierto
            self.abierto = False
        return self.abierto

    def forzar_apertura(self):
        """Simula un evento de apertura forzada o no autorizada.
        
        Este método establece el estado del sensor como abierto y genera una alerta de seguridad,
        lo que podría representar una entrada no autorizada o una apertura de emergencia.
        """
        self.abierto = True
        print(f"¡ALERTA! Sensor [{self.id_sensor}] en '{self.ubicacion}' ha sido ABIERTO.")

    def obtener_estado_str(self):
        """Obtiene una representación en texto del estado actual del sensor de apertura.
        
        Returns:
            str: Cadena de texto describiendo el estado actual del sensor (ABIERTO/Cerrado),
                 incluyendo su ID y ubicación.
        """
        estado = "ABIERTO" if self.abierto else "Cerrado"
        return f"Sensor Apertura [{self.id_sensor}] ({self.ubicacion}): {estado}"
        
    def publicar_en_aws_iot(self):
        """Publica el estado del sensor de apertura en AWS IoT Core mediante MQTT.
        
        Utiliza el script pub.py para enviar el estado actual del sensor de apertura
        al broker MQTT de AWS IoT Core. Construye un mensaje JSON con todos los datos
        relevantes del sensor y los envía al tópico correspondiente.
        
        Returns:
            bool: True si la publicación fue exitosa, False en caso contrario.
        """
        # Determinar la ruta al script pub.py (script de publicación MQTT)
        pub_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "gatewayPUJC", "Gateway", "pub.py")
                                
        # Ruta base para los certificados de autenticación AWS IoT
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gatewayPUJC")
        
        # Crear el mensaje JSON con los datos del sensor
        mensaje = {
            "sensor": f"apertura_{self.id_sensor}",     # Identificador único
            "value": 1 if self.abierto else 0,        # 1=abierto, 0=cerrado
            "unit": "estado",                         # Unidad de medida
            "ubicacion": self.ubicacion,              # Ubicación física
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())  # Marca de tiempo ISO 8601
        }
        
        # Construir el comando para ejecutar el script de publicación
        comando = [
            "python",                                   # Intérprete Python
            pub_script,                                # Script de publicación MQTT
            "--endpoint", "a18v3fuy20t61j-ats.iot.us-east-1.amazonaws.com",  # Endpoint AWS IoT
            "--ca_file", os.path.join(base_path, "root-CA.crt"),            # Certificado CA raíz
            "--cert", os.path.join(base_path, "GatewayLab_PUJC_Palmas_33_GW001.cert.pem"),    # Certificado cliente
            "--key", os.path.join(base_path, "GatewayLab_PUJC_Palmas_33_GW001.private.key"),  # Clave privada
            "--client_id", f"sensor_apertura_{self.id_sensor}",   # ID de cliente MQTT
            "--topic", f"data/retail/sensors/apertura/{self.id_sensor}",  # Tópico MQTT para sensores de apertura
            "--count", "1",                            # Envío único (no continuo)
            "--message", json.dumps(mensaje)            # Mensaje serializado como JSON
        ]
        
        # Ejecutar el comando y capturar su resultado
        print(f"Publicando estado del sensor de apertura {self.id_sensor}: {'Abierto' if self.abierto else 'Cerrado'}")
        resultado = subprocess.run(comando, cwd=base_path)
        
        # Devolver True si el comando se ejecutó correctamente (código de salida 0)
        return resultado.returncode == 0

# ========================================================================
# Bloque principal para ejecución independiente del sensor de apertura
# ========================================================================

if __name__ == "__main__":
    """Punto de entrada principal cuando se ejecuta este script directamente.
    
    Este bloque permite ejecutar el simulador de sensor de apertura de forma independiente.
    Crea una instancia del sensor para una puerta específica y realiza ciclos de simulación,
    generando lecturas aleatorias que reflejan el comportamiento real del sensor en operación.
    """
    # Inicializar un sensor de apertura para la puerta de emergencia del almacén
    sensor = SensorApertura("APR001", "Puerta Emergencia Almacén")
    
    try:
        # Iniciar ciclo infinito de simulación
        while True:
            # Simular una lectura del sensor con probabilidades aleatorias
            sensor.simular_lectura()
            # Mostrar el estado actual del sensor
            print(sensor.obtener_estado_str())
            
            # Publicar el estado en AWS IoT Core
            exito = sensor.publicar_en_aws_iot()
            
            # Informar sobre el resultado de la publicación
            if exito:
                print("Publicación exitosa en AWS IoT")
            else:
                print("Error al publicar en AWS IoT")
                
            # Esperar 10 segundos antes de la siguiente lectura
            time.sleep(10)
            
    except KeyboardInterrupt:
        # Capturar Ctrl+C para terminar el programa de forma limpia
        print("\nSensor detenido por el usuario.")
