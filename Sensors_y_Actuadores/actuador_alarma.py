############################################################
# Simulador de Actuador de Alarma para Sistema IoT Retail #
# Simula una alarma que puede ser activada remotamente    #
# y envía su estado al broker MQTT de AWS IoT Core       #
############################################################

import random
import time
import subprocess  # Para ejecutar el script de publicación MQTT
import os         # Para manejo de rutas de archivos
import json       # Para formateo de mensajes JSON

class ActuadorAlarma:
    """Clase que simula un actuador de alarma en un entorno retail.
    
    Esta clase simula el comportamiento de un sistema de alarma que puede estar
    compuesto por sirenas, luces estroboscópicas u otros elementos de alerta.
    El actuador puede ser activado o desactivado y publicar su estado en AWS IoT Core.
    """
    
    def __init__(self, id_actuador, tipo="Sirena y Luz Estroboscópica", ubicacion="General Tienda"):
        """Inicializa un nuevo actuador de alarma.
        
        Args:
            id_actuador (str): Identificador único del actuador (ej: 'ALM001')
            tipo (str): Tipo específico de alarma (por defecto: 'Sirena y Luz Estroboscópica')
            ubicacion (str): Ubicación física del actuador (por defecto: 'General Tienda')
        """
        self.id_actuador = id_actuador
        self.tipo = tipo
        self.ubicacion = ubicacion
        self.activa = False  # Estado inicial: desactivada
        print(f"Actuador de Alarma [{self.id_actuador}] ({self.tipo}) inicializado en: {self.ubicacion}")

    def activar(self):
        """Activa la alarma si no está ya activada.
        
        Cambia el estado de la alarma a activa y muestra un mensaje de confirmación.
        Si la alarma ya estaba activa, simplemente muestra un mensaje informativo.
        """
        if not self.activa:
            self.activa = True
            print(f"¡¡¡ ACTUADOR ALARMA [{self.id_actuador}] ACTIVADA ({self.tipo} en {self.ubicacion}) !!!")
        else:
            print(f"Actuador Alarma [{self.id_actuador}] ya está activa.")

    def desactivar(self):
        """Desactiva la alarma si está activa.
        
        Cambia el estado de la alarma a inactiva y muestra un mensaje de confirmación.
        Si la alarma ya estaba inactiva, simplemente muestra un mensaje informativo.
        """
        if self.activa:
            self.activa = False
            print(f"Actuador Alarma [{self.id_actuador}] DESACTIVADA.")
        else:
            print(f"Actuador Alarma [{self.id_actuador}] ya está desactivada.")

    def obtener_estado_str(self):
        """Obtiene una representación en texto del estado actual de la alarma.
        
        Returns:
            str: Cadena de texto describiendo el estado actual de la alarma (ACTIVA/INACTIVA),
                 incluyendo su ID, tipo y ubicación.
        """
        estado = "ACTIVA" if self.activa else "INACTIVA"
        return f"Actuador Alarma [{self.id_actuador}] ({self.tipo} en {self.ubicacion}): {estado}"
        
    def publicar_en_aws_iot(self):
        """Publica el estado del actuador en AWS IoT Core mediante MQTT.
        
        Utiliza el script pub.py para enviar el estado actual del actuador de alarma
        al broker MQTT de AWS IoT Core. Construye un mensaje JSON con todos los datos
        relevantes del actuador y los envía al tópico correspondiente.
        
        Returns:
            bool: True si la publicación fue exitosa, False en caso contrario.
        """
        # Determinar la ruta al script pub.py (script de publicación MQTT)
        pub_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "gatewayPUJC", "Gateway", "pub.py")
                                
        # Ruta base para los certificados de autenticación AWS IoT
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gatewayPUJC")
        
        # Crear el mensaje JSON con los datos del actuador
        mensaje = {
            "sensor": f"alarma_{self.id_actuador}",      # Identificador único
            "value": 1 if self.activa else 0,           # 1=activada, 0=desactivada
            "unit": "estado",                           # Unidad de medida
            "tipo": self.tipo,                          # Tipo de alarma
            "ubicacion": self.ubicacion,                # Ubicación física
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
            "--client_id", f"actuador_alarma_{self.id_actuador}",   # ID de cliente MQTT
            "--topic", f"data/retail/actuadores/alarma/{self.id_actuador}",  # Tópico MQTT
            "--count", "1",                            # Envío único (no continuo)
            "--message", json.dumps(mensaje)            # Mensaje serializado como JSON
        ]
        
        # Ejecutar el comando y capturar su resultado
        print(f"Publicando estado del actuador de alarma {self.id_actuador}: {'Activa' if self.activa else 'Inactiva'}")
        resultado = subprocess.run(comando, cwd=base_path)
        
        # Devolver True si el comando se ejecutó correctamente (código de salida 0)
        return resultado.returncode == 0

# ========================================================================
# Bloque principal para ejecución independiente del actuador de alarma
# ========================================================================

if __name__ == "__main__":
    """Punto de entrada principal cuando se ejecuta este script directamente.
    
    Este bloque permite ejecutar el simulador de actuador de alarma de forma independiente.
    Crea una instancia del actuador y realiza ciclos de simulación, activando y desactivando
    la alarma periódicamente, y publicando su estado en AWS IoT Core.
    """
    # Inicializar un actuador de alarma con ID ALM001 ubicado en la tienda completa
    alarma = ActuadorAlarma("ALM001", ubicacion="Tienda Completa")
    
    try:
        # Iniciar ciclo de simulación
        ciclo = 0
        while True:
            ciclo += 1
            print(f"--- Ciclo {ciclo} ---")
            
            # Simular eventos según el número de ciclo
            # La alarma se activa cada 5 ciclos
            if ciclo % 5 == 0:
                print("\nEVENTO: Activando alarma")
                alarma.activar()
            
            # La alarma se desactiva cada 10 ciclos
            if ciclo % 10 == 0:
                print("\nEVENTO: Desactivando alarma")
                alarma.desactivar()
            
            # Mostrar el estado actual y publicarlo en AWS IoT Core
            print(alarma.obtener_estado_str())
            exito = alarma.publicar_en_aws_iot()
            
            # Informar sobre el resultado de la publicación
            if exito:
                print("Publicación exitosa en AWS IoT")
            else:
                print("Error al publicar en AWS IoT")
                
            # Esperar 10 segundos antes del siguiente ciclo
            time.sleep(10)
            
    except KeyboardInterrupt:
        # Capturar Ctrl+C para terminar el programa de forma limpia
        print("\nActuador detenido por el usuario.")
