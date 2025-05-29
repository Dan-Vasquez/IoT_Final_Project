import random
import time
import subprocess
import os
import json

class ActuadorAlarma:
    def __init__(self, id_actuador, tipo="Sirena y Luz Estroboscópica", ubicacion="General Tienda"):
        self.id_actuador = id_actuador
        self.tipo = tipo
        self.ubicacion = ubicacion
        self.activa = False
        print(f"Actuador de Alarma [{self.id_actuador}] ({self.tipo}) inicializado en: {self.ubicacion}")

    def activar(self):
        if not self.activa:
            self.activa = True
            print(f"¡¡¡ ACTUADOR ALARMA [{self.id_actuador}] ACTIVADA ({self.tipo} en {self.ubicacion}) !!!")
        else:
            print(f"Actuador Alarma [{self.id_actuador}] ya está activa.")

    def desactivar(self):
        if self.activa:
            self.activa = False
            print(f"Actuador Alarma [{self.id_actuador}] DESACTIVADA.")
        else:
            print(f"Actuador Alarma [{self.id_actuador}] ya está desactivada.")

    def obtener_estado_str(self):
        estado = "ACTIVA" if self.activa else "INACTIVA"
        return f"Actuador Alarma [{self.id_actuador}] ({self.tipo} en {self.ubicacion}): {estado}"
        
    def publicar_en_aws_iot(self):
        """Publica el estado del actuador en AWS IoT Core"""
        # Determinar la ruta al script pub.py
        pub_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "gatewayPUJC", "Gateway", "pub.py")
                                
        # Ruta base para los certificados
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gatewayPUJC")
        
        # Crear el mensaje JSON con los datos del actuador
        mensaje = {
            "sensor": f"alarma_{self.id_actuador}",
            "value": 1 if self.activa else 0,
            "unit": "estado",
            "tipo": self.tipo,
            "ubicacion": self.ubicacion,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        # Construir los parámetros para la publicación
        comando = [
            "python", 
            pub_script,
            "--endpoint", "a18v3fuy20t61j-ats.iot.us-east-1.amazonaws.com",
            "--ca_file", os.path.join(base_path, "root-CA.crt"),
            "--cert", os.path.join(base_path, "GatewayLab_PUJC_Palmas_33_GW001.cert.pem"),
            "--key", os.path.join(base_path, "GatewayLab_PUJC_Palmas_33_GW001.private.key"),
            "--client_id", f"actuador_alarma_{self.id_actuador}",
            "--topic", f"data/retail/actuadores/alarma/{self.id_actuador}",
            "--count", "1",
            "--message", json.dumps(mensaje)
        ]
        
        # Ejecutar el comando
        print(f"Publicando estado del actuador de alarma {self.id_actuador}: {'Activa' if self.activa else 'Inactiva'}")
        resultado = subprocess.run(comando, cwd=base_path)
        
        return resultado.returncode == 0

# Para ejecutar el actuador de forma independiente
if __name__ == "__main__":
    # Inicializar actuador
    alarma = ActuadorAlarma("ALM001", ubicacion="Tienda Completa")
    
    try:
        ciclo = 0
        while True:
            ciclo += 1
            print(f"--- Ciclo {ciclo} ---")
            
            # Simular eventos según el ciclo
            if ciclo % 5 == 0:
                print("\nEVENTO: Activando alarma")
                alarma.activar()
            
            if ciclo % 10 == 0:
                print("\nEVENTO: Desactivando alarma")
                alarma.desactivar()
            
            # Publicar estado en AWS IoT
            print(alarma.obtener_estado_str())
            exito = alarma.publicar_en_aws_iot()
            if exito:
                print("Publicación exitosa en AWS IoT")
            else:
                print("Error al publicar en AWS IoT")
                
            # Esperar antes de la siguiente lectura
            time.sleep(10)  # 10 segundos entre lecturas
            
    except KeyboardInterrupt:
        print("\nActuador detenido por el usuario.")
