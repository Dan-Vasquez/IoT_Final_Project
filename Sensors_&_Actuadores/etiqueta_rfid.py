import random
import time
import subprocess
import os
import json

class EtiquetaRFID:
    def __init__(self, id_etiqueta, nombre_producto):
        self.id_etiqueta = id_etiqueta
        self.nombre_producto = nombre_producto
        self.alarma_activa = False
        self.pagado = False # El producto no ha sido pagado inicialmente
        print(f"Etiqueta RFID [{self.id_etiqueta}] asignada a: {self.nombre_producto}")

    def simular_paso_por_salida(self):
        """Simula el producto pasando por el arco de salida.
        Si no está pagado, la alarma se activa.
        """
        if not self.pagado:
            self.alarma_activa = True
            print(f"¡ALARMA RFID! Producto '{self.nombre_producto}' [{self.id_etiqueta}] saliendo sin pagar.")
        else:
            self.alarma_activa = False
            print(f"Producto '{self.nombre_producto}' [{self.id_etiqueta}] saliendo (pagado). Alarma desactivada.")
        return self.alarma_activa

    def marcar_como_pagado(self):
        """Simula el proceso de pago, que desactivaría la alarma."""
        self.pagado = True
        self.alarma_activa = False
        print(f"Producto '{self.nombre_producto}' [{self.id_etiqueta}] marcado como pagado. Alarma desactivada.")

    def obtener_estado_str(self):
        estado_alarma = "ALARMA ACTIVA" if self.alarma_activa else "Alarma Inactiva"
        estado_pago = "Pagado" if self.pagado else "No Pagado"
        return f"Etiqueta RFID [{self.id_etiqueta}] ({self.nombre_producto}): {estado_alarma} ({estado_pago})"
        
    def publicar_en_aws_iot(self):
        """Publica el estado del sensor en AWS IoT Core"""
        # Determinar la ruta al script pub.py
        pub_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "gatewayPUJC", "Gateway", "pub.py")
                                
        # Ruta base para los certificados
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gatewayPUJC")
        
        # Crear el mensaje JSON con los datos del sensor
        mensaje = {
            "sensor": f"rfid_{self.id_etiqueta}",
            "value": 1 if self.alarma_activa else 0,
            "unit": "estado",
            "producto": self.nombre_producto,
            "pagado": self.pagado,
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
            "--client_id", f"sensor_rfid_{self.id_etiqueta}",
            "--topic", f"data/retail/sensors/rfid/{self.id_etiqueta}",
            "--count", "1",
            "--message", json.dumps(mensaje)
        ]
        
        # Ejecutar el comando
        print(f"Publicando estado de etiqueta RFID {self.id_etiqueta}: Alarma {'Activa' if self.alarma_activa else 'Inactiva'}")
        resultado = subprocess.run(comando, cwd=base_path)
        
        return resultado.returncode == 0

# Para ejecutar el sensor de forma independiente
if __name__ == "__main__":
    # Inicializar sensor
    etiqueta = EtiquetaRFID("RFID001", "Smart TV 55 pulgadas")
    
    try:
        ciclo = 0
        while True:
            ciclo += 1
            print(f"--- Ciclo {ciclo} ---")
            
            # Simular eventos según el ciclo
            if ciclo % 5 == 0:
                print("\nEVENTO: Producto marcado como pagado")
                etiqueta.marcar_como_pagado()
            
            if ciclo % 6 == 0:
                print("\nEVENTO: Producto pasando por la salida")
                etiqueta.simular_paso_por_salida()
            
            # Publicar estado en AWS IoT
            print(etiqueta.obtener_estado_str())
            exito = etiqueta.publicar_en_aws_iot()
            if exito:
                print("Publicación exitosa en AWS IoT")
            else:
                print("Error al publicar en AWS IoT")
                
            # Esperar antes de la siguiente lectura
            time.sleep(10)  # 10 segundos entre lecturas
            
    except KeyboardInterrupt:
        print("\nSensor detenido por el usuario.")
