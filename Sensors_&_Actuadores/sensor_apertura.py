import random
import time
import subprocess
import os
import json

class SensorApertura:
    def __init__(self, id_sensor, ubicacion="Puerta Desconocida"):
        self.id_sensor = id_sensor
        self.ubicacion = ubicacion
        self.abierto = False # Comienza cerrado
        print(f"Sensor de Apertura [{self.id_sensor}] inicializado para: {self.ubicacion}")

    def simular_lectura(self):
        """Simula la apertura o cierre.
        Pequeña probabilidad de abrirse si está cerrado.
        Mayor probabilidad de cerrarse si está abierto (simulando que alguien lo cierra).
        """
        if not self.abierto and random.random() < 0.05: # 5% de probabilidad de abrirse
            self.abierto = True
        elif self.abierto and random.random() < 0.6: # 60% de probabilidad de cerrarse si estaba abierto
            self.abierto = False
        return self.abierto

    def forzar_apertura(self):
        """Simula un evento de apertura forzada."""
        self.abierto = True
        print(f"¡ALERTA! Sensor [{self.id_sensor}] en '{self.ubicacion}' ha sido ABIERTO.")

    def obtener_estado_str(self):
        estado = "ABIERTO" if self.abierto else "Cerrado"
        return f"Sensor Apertura [{self.id_sensor}] ({self.ubicacion}): {estado}"
        
    def publicar_en_aws_iot(self):
        """Publica el estado del sensor en AWS IoT Core"""
        # Determinar la ruta al script pub.py
        pub_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "gatewayPUJC", "Gateway", "pub.py")
                                
        # Ruta base para los certificados
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gatewayPUJC")
        
        # Crear el mensaje JSON con los datos del sensor
        mensaje = {
            "sensor": f"apertura_{self.id_sensor}",
            "value": 1 if self.abierto else 0,
            "unit": "estado",
            "ubicacion": self.ubicacion,
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
            "--client_id", f"sensor_apertura_{self.id_sensor}",
            "--topic", f"data/retail/sensors/apertura/{self.id_sensor}",
            "--count", "1",
            "--message", json.dumps(mensaje)
        ]
        
        # Ejecutar el comando
        print(f"Publicando estado del sensor de apertura {self.id_sensor}: {'Abierto' if self.abierto else 'Cerrado'}")
        resultado = subprocess.run(comando, cwd=base_path)
        
        return resultado.returncode == 0

# Para ejecutar el sensor de forma independiente
if __name__ == "__main__":
    # Inicializar sensor
    sensor = SensorApertura("APE001", "Puerta Emergencia Almacén")
    
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
