import random
import time
import subprocess
import os
import json

class SensorMovimiento:
    def __init__(self, id_sensor, area="Desconocida"):
        self.id_sensor = id_sensor
        self.area = area
        self.movimiento_detectado = False
        print(f"Sensor de Movimiento [{self.id_sensor}] inicializado para el área: {self.area}")

    def simular_lectura(self):
        """Simula la detección de movimiento.
        Hay una pequeña probabilidad de que se detecte movimiento.
        """
        if random.random() < 0.1: # 10% de probabilidad de detectar movimiento
            self.movimiento_detectado = True
        else:
            # Si ya estaba detectando, hay una probabilidad de que deje de detectar
            if self.movimiento_detectado and random.random() < 0.7:
                 self.movimiento_detectado = False
        return self.movimiento_detectado

    def obtener_estado_str(self):
        estado = "MOVIMIENTO DETECTADO" if self.movimiento_detectado else "Sin movimiento"
        return f"Sensor Movimiento [{self.id_sensor}] ({self.area}): {estado}"
        
    def publicar_en_aws_iot(self):
        """Publica el estado del sensor en AWS IoT Core"""
        # Determinar la ruta al script pub.py
        pub_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "gatewayPUJC", "Gateway", "pub.py")
                                
        # Ruta base para los certificados
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gatewayPUJC")
        
        # Crear el mensaje JSON con los datos del sensor
        mensaje = {
            "sensor": f"movimiento_{self.id_sensor}",
            "value": 1 if self.movimiento_detectado else 0,
            "unit": "estado",
            "area": self.area,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        # Construir los parámetros para la publicación
        comando = [
            "python", 
            pub_script,
            "--endpoint", "a1tq9r6f8r1tbb-ats.iot.us-east-1.amazonaws.com",
            "--ca_file", os.path.join(base_path, "root-CA.crt"),
            "--cert", os.path.join(base_path, "GatewayLab_PUJC_Palmas_33_GW001.cert.pem"),
            "--key", os.path.join(base_path, "GatewayLab_PUJC_Palmas_33_GW001.private.key"),
            "--client_id", f"sensor_movimiento_{self.id_sensor}",
            "--topic", f"data/retail/sensors/movimiento/{self.id_sensor}",
            "--count", "1",
            "--message", json.dumps(mensaje)
        ]
        
        # Ejecutar el comando
        print(f"Publicando estado del sensor de movimiento {self.id_sensor}: {'Movimiento' if self.movimiento_detectado else 'Sin movimiento'}")
        resultado = subprocess.run(comando, cwd=base_path)
        
        return resultado.returncode == 0

# Para ejecutar el sensor de forma independiente
if __name__ == "__main__":
    # Inicializar sensor
    sensor = SensorMovimiento("MOV001", "Almacén Principal")
    
    try:
        while True:
            # Simular una lectura
            sensor.simular_lectura()
            print(sensor.obtener_estado_str())
            
            # Publicar en AWS IoT
            exito = sensor.publicar_en_aws_iot()
            if exito:
                print("Publicación exitosa en AWS IoT")
            else:
                print("Error al publicar en AWS IoT")
                
            # Esperar antes de la siguiente lectura
            time.sleep(10)  # 10 segundos entre lecturas
            
    except KeyboardInterrupt:
        print("\nSensor detenido por el usuario.")
