import random
import time
import subprocess
import os
import json

class ActuadorPuertaAutomatica:
    def __init__(self, id_actuador, ubicacion="Entrada Principal"):
        self.id_actuador = id_actuador
        self.ubicacion = ubicacion
        self.abierta = False # Comienza cerrada
        print(f"Actuador de Puerta Automática [{self.id_actuador}] inicializado en: {self.ubicacion}")

    def abrir(self):
        if not self.abierta:
            self.abierta = True
            print(f"Actuador Puerta Automática [{self.id_actuador}] ({self.ubicacion}): ABRIENDO...")
        else:
            print(f"Actuador Puerta Automática [{self.id_actuador}] ({self.ubicacion}): ya está abierta.")

    def cerrar(self):
        if self.abierta:
            self.abierta = False
            print(f"Actuador Puerta Automática [{self.id_actuador}] ({self.ubicacion}): CERRANDO...")
        else:
            print(f"Actuador Puerta Automática [{self.id_actuador}] ({self.ubicacion}): ya está cerrada.")

    def obtener_estado_str(self):
        estado = "ABIERTA" if self.abierta else "CERRADA"
        return f"Actuador P.Automática [{self.id_actuador}] ({self.ubicacion}): {estado}"
        
    def publicar_en_aws_iot(self):
        """Publica el estado del actuador en AWS IoT Core"""
        # Determinar la ruta al script pub.py
        pub_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "gatewayPUJC", "Gateway", "pub.py")
                                
        # Ruta base para los certificados
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gatewayPUJC")
        
        # Crear el mensaje JSON con los datos del actuador
        mensaje = {
            "sensor": f"puerta_{self.id_actuador}",
            "value": 1 if self.abierta else 0,
            "unit": "estado",
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
            "--client_id", f"actuador_puerta_{self.id_actuador}",
            "--topic", f"data/retail/actuadores/puerta/{self.id_actuador}",
            "--count", "1",
            "--message", json.dumps(mensaje)
        ]
        
        # Ejecutar el comando
        print(f"Publicando estado del actuador de puerta {self.id_actuador}: {'Abierta' if self.abierta else 'Cerrada'}")
        resultado = subprocess.run(comando, cwd=base_path)
        
        return resultado.returncode == 0

# Para ejecutar el actuador de forma independiente
if __name__ == "__main__":
    # Inicializar actuador
    puerta = ActuadorPuertaAutomatica("PTA001", "Entrada Tienda")
    
    try:
        ciclo = 0
        while True:
            ciclo += 1
            print(f"--- Ciclo {ciclo} ---")
            
            # Simular eventos según el ciclo
            if ciclo % 3 == 0:
                print("\nEVENTO: Detectando movimiento en entrada, abriendo puerta")
                puerta.abrir()
            
            if ciclo % 4 == 0:
                print("\nEVENTO: Sin movimiento en entrada, cerrando puerta")
                puerta.cerrar()
            
            # Publicar estado en AWS IoT
            print(puerta.obtener_estado_str())
            exito = puerta.publicar_en_aws_iot()
            if exito:
                print("Publicación exitosa en AWS IoT")
            else:
                print("Error al publicar en AWS IoT")
                
            # Esperar antes de la siguiente lectura
            time.sleep(10)  # 10 segundos entre lecturas
            
    except KeyboardInterrupt:
        print("\nActuador detenido por el usuario.")
