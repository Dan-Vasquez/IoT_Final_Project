############################################################
# Simulador de Sensor de Movimiento para Sistema IoT Retail #
# Simula un sensor PIR que detecta movimiento en un área    #
# y publica eventos en AWS IoT Core                        #
############################################################

import random  # Para simulación de eventos aleatorios
import time    # Para timestamping y sleep
import subprocess  # Para ejecutar el script de publicación MQTT
import os     # Para manejo de rutas de archivos
import json   # Para formateo de mensajes JSON

class SensorMovimiento:
    """Clase que simula un sensor de movimiento (PIR) en un entorno retail.
    
    Esta clase simula el comportamiento de un sensor de movimiento infrarrojo pasivo (PIR)
    que detecta cuando hay movimiento en un área determinada. El sensor puede enviar
    alertas de movimiento y publicar su estado en AWS IoT Core para monitoreo en tiempo real.
    """
    
    def __init__(self, id_sensor, area="Desconocida"):
        """Inicializa un nuevo sensor de movimiento.
        
        Args:
            id_sensor (str): Identificador único del sensor (ej: 'MOV001')
            area (str): Área física donde está instalado el sensor (por defecto: 'Desconocida')
        """
        self.id_sensor = id_sensor
        self.area = area
        self.movimiento_detectado = False  # Estado inicial: sin movimiento
        print(f"Sensor de Movimiento [{self.id_sensor}] inicializado para el área: {self.area}")

    def simular_lectura(self):
        """Simula una lectura del sensor con probabilidades aleatorias de detección de movimiento.
        
        Este método simula el comportamiento real de un sensor PIR, con una baja probabilidad
        de detectar movimiento (representando a alguien entrando en el área monitoreada) y una
        probabilidad más alta de dejar de detectar movimiento una vez que ya lo estaba detectando
        (representando que la persona sale del área o se queda quieta).
        
        Returns:
            bool: El estado actual del sensor después de la simulación (True=movimiento detectado, False=sin movimiento).
        """
        if random.random() < 0.1:  # 10% de probabilidad de detectar movimiento nuevo
            self.movimiento_detectado = True
        else:
            # Si ya estaba detectando, 70% de probabilidad de que el movimiento cese
            if self.movimiento_detectado and random.random() < 0.7:
                 self.movimiento_detectado = False
        return self.movimiento_detectado

    def obtener_estado_str(self):
        """Obtiene una representación en texto del estado actual del sensor de movimiento.
        
        Returns:
            str: Cadena de texto describiendo el estado actual del sensor (MOVIMIENTO DETECTADO/Sin movimiento),
                 incluyendo su ID y área monitoreada.
        """
        estado = "MOVIMIENTO DETECTADO" if self.movimiento_detectado else "Sin movimiento"
        return f"Sensor Movimiento [{self.id_sensor}] ({self.area}): {estado}"
        
    def publicar_en_aws_iot(self):
        """Publica el estado del sensor de movimiento en AWS IoT Core mediante MQTT.
        
        Utiliza el script pub.py para enviar el estado actual del sensor de movimiento
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
            "sensor": f"movimiento_{self.id_sensor}",     # Identificador único
            "value": 1 if self.movimiento_detectado else 0,  # 1=movimiento detectado, 0=sin movimiento
            "unit": "estado",                           # Unidad de medida
            "area": self.area,                          # Área física monitoreada
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
            "--client_id", f"sensor_movimiento_{self.id_sensor}",   # ID de cliente MQTT
            "--topic", f"data/retail/sensors/movimiento/{self.id_sensor}",  # Tópico MQTT para sensores de movimiento
            "--count", "1",                            # Envío único (no continuo)
            "--message", json.dumps(mensaje)            # Mensaje serializado como JSON
        ]
        
        # Ejecutar el comando y capturar su resultado
        print(f"Publicando estado del sensor de movimiento {self.id_sensor}: {'Movimiento' if self.movimiento_detectado else 'Sin movimiento'}")
        resultado = subprocess.run(comando, cwd=base_path)
        
        # Devolver True si el comando se ejecutó correctamente (código de salida 0)
        return resultado.returncode == 0

# ========================================================================
# Bloque principal para ejecución independiente del sensor de movimiento
# ========================================================================

if __name__ == "__main__":
    """Punto de entrada principal cuando se ejecuta este script directamente.
    
    Este bloque permite ejecutar el simulador de sensor de movimiento de forma independiente.
    Crea una instancia del sensor para un área específica y realiza ciclos de simulación,
    generando lecturas aleatorias que reflejan el comportamiento real del sensor en operación.
    """
    # Inicializar un sensor de movimiento para el almacén principal
    sensor = SensorMovimiento("MOV001", "Almacén Principal")
    
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
