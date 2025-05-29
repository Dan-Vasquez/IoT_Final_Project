############################################################
# Simulador de Etiqueta RFID para Sistema IoT Retail     #
# Simula una etiqueta RFID antirrobo de producto que     #
# puede activar alarmas y publicar eventos en AWS IoT     #
############################################################

import random  # Para simulación de eventos aleatorios
import time    # Para timestamping y sleep
import subprocess  # Para ejecutar el script de publicación MQTT
import os     # Para manejo de rutas de archivos
import json   # Para formateo de mensajes JSON

class EtiquetaRFID:
    """Clase que simula una etiqueta RFID antirrobo para productos retail.
    
    Esta clase simula el comportamiento de una etiqueta RFID que se coloca en productos
    para prevenir robos. La etiqueta tiene dos estados principales: pagado/no pagado
    y alarma activa/inactiva. Cuando un producto con la etiqueta no pagada pasa por
    un arco de seguridad en la salida, la alarma se activa.
    """
    
    def __init__(self, id_etiqueta, nombre_producto):
        """Inicializa una nueva etiqueta RFID para un producto.
        
        Args:
            id_etiqueta (str): Identificador único de la etiqueta RFID (ej: 'RFID001')
            nombre_producto (str): Nombre del producto al que está asignada la etiqueta
        """
        self.id_etiqueta = id_etiqueta
        self.nombre_producto = nombre_producto
        self.alarma_activa = False  # Estado inicial: alarma desactivada
        self.pagado = False         # Estado inicial: producto no pagado
        print(f"Etiqueta RFID [{self.id_etiqueta}] asignada a: {self.nombre_producto}")

    def simular_paso_por_salida(self):
        """Simula el producto pasando por el arco de seguridad en la salida.
        
        Cuando un producto con una etiqueta RFID pasa por el arco de seguridad en la salida de la tienda,
        se verifica si ha sido pagado. Si no ha sido pagado, se activa la alarma antirrobo.
        
        Returns:
            bool: True si la alarma se activó (producto no pagado), False en caso contrario
        """
        if not self.pagado:
            # Si el producto no está pagado, activar la alarma
            self.alarma_activa = True
            print(f"¡ALARMA RFID! Producto '{self.nombre_producto}' [{self.id_etiqueta}] saliendo sin pagar.")
        else:
            # Si el producto está pagado, la alarma permanece inactiva
            self.alarma_activa = False
            print(f"Producto '{self.nombre_producto}' [{self.id_etiqueta}] saliendo (pagado). Alarma desactivada.")
        return self.alarma_activa

    def marcar_como_pagado(self):
        """Simula el proceso de pago en caja registradora o terminal de pago.
        
        Cuando un producto es pagado en la caja, su etiqueta RFID se marca como pagada y
        se desactiva la alarma, permitiendo que pueda salir de la tienda sin activar
        el sistema de seguridad.
        """
        self.pagado = True
        self.alarma_activa = False
        print(f"Producto '{self.nombre_producto}' [{self.id_etiqueta}] marcado como pagado. Alarma desactivada.")

    def obtener_estado_str(self):
        """Obtiene una representación en texto del estado actual de la etiqueta RFID.
        
        Returns:
            str: Cadena de texto describiendo el estado actual de la etiqueta,
                 incluyendo su ID, producto asociado, estado de alarma y estado de pago.
        """
        estado_alarma = "ALARMA ACTIVA" if self.alarma_activa else "Alarma Inactiva"
        estado_pago = "Pagado" if self.pagado else "No Pagado"
        return f"Etiqueta RFID [{self.id_etiqueta}] ({self.nombre_producto}): {estado_alarma} ({estado_pago})"
        
    def publicar_en_aws_iot(self):
        """Publica el estado de la etiqueta RFID en AWS IoT Core mediante MQTT.
        
        Utiliza el script pub.py para enviar el estado actual de la etiqueta RFID
        al broker MQTT de AWS IoT Core. Construye un mensaje JSON con todos los datos
        relevantes de la etiqueta, incluyendo si está pagada y si la alarma está activa.
        
        Returns:
            bool: True si la publicación fue exitosa, False en caso contrario.
        """
        # Determinar la ruta al script pub.py (script de publicación MQTT)
        pub_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "gatewayPUJC", "Gateway", "pub.py")
                                
        # Ruta base para los certificados de autenticación AWS IoT
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gatewayPUJC")
        
        # Crear el mensaje JSON con los datos de la etiqueta RFID
        mensaje = {
            "sensor": f"rfid_{self.id_etiqueta}",      # Identificador único
            "value": 1 if self.alarma_activa else 0,  # 1=alarma activa, 0=alarma inactiva
            "unit": "estado",                         # Unidad de medida
            "producto": self.nombre_producto,          # Nombre del producto etiquetado
            "pagado": self.pagado,                    # Estado de pago del producto
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
            "--client_id", f"sensor_rfid_{self.id_etiqueta}",   # ID de cliente MQTT
            "--topic", f"data/retail/sensors/rfid/{self.id_etiqueta}",  # Tópico MQTT para sensores RFID
            "--count", "1",                            # Envío único (no continuo)
            "--message", json.dumps(mensaje)            # Mensaje serializado como JSON
        ]
        
        # Ejecutar el comando y capturar su resultado
        print(f"Publicando estado de etiqueta RFID {self.id_etiqueta}: Alarma {'Activa' if self.alarma_activa else 'Inactiva'}")
        resultado = subprocess.run(comando, cwd=base_path)
        
        # Devolver True si el comando se ejecutó correctamente (código de salida 0)
        return resultado.returncode == 0

# ========================================================================
# Bloque principal para ejecución independiente de la etiqueta RFID
# ========================================================================

if __name__ == "__main__":
    """Punto de entrada principal cuando se ejecuta este script directamente.
    
    Este bloque permite ejecutar el simulador de etiqueta RFID de forma independiente.
    Crea una instancia de etiqueta para un producto específico y realiza ciclos de simulación,
    alternando entre marcar el producto como pagado y simular su paso por el arco de seguridad.
    """
    # Inicializar una etiqueta RFID para un producto electrónico de alto valor
    etiqueta = EtiquetaRFID("RFID001", "Smart TV 55 pulgadas")
    
    try:
        # Iniciar ciclo de simulación
        ciclo = 0
        while True:
            ciclo += 1
            print(f"--- Ciclo {ciclo} ---")
            
            # Cada 5 ciclos: simular el pago del producto en caja
            if ciclo % 5 == 0:
                print("\nEVENTO: Producto marcado como pagado")
                etiqueta.marcar_como_pagado()
            
            # Cada 6 ciclos: simular que el producto pasa por el arco de seguridad
            if ciclo % 6 == 0:
                print("\nEVENTO: Producto pasando por la salida")
                etiqueta.simular_paso_por_salida()
            
            # Mostrar el estado actual y publicarlo en AWS IoT Core
            print(etiqueta.obtener_estado_str())
            exito = etiqueta.publicar_en_aws_iot()
            
            # Informar sobre el resultado de la publicación
            if exito:
                print("Publicación exitosa en AWS IoT")
            else:
                print("Error al publicar en AWS IoT")
                
            # Esperar 10 segundos antes del siguiente ciclo
            time.sleep(10)
            
    except KeyboardInterrupt:
        # Capturar Ctrl+C para terminar el programa de forma limpia
        print("\nSensor detenido por el usuario.")
