############################################################
# Simulador de Actuador de Puerta para Sistema IoT Retail #
# Simula una puerta automática que puede ser abierta o   #
# cerrada remotamente y publica su estado en AWS IoT Core #
############################################################

import random  # Para simulación de eventos aleatorios
import time    # Para timestamping y sleep
import subprocess  # Para ejecutar el script de publicación MQTT
import os     # Para manejo de rutas de archivos
import json   # Para formateo de mensajes JSON

class ActuadorPuertaAutomatica:
    """Clase que simula un actuador de puerta automática en un entorno retail.
    
    Esta clase simula el comportamiento de una puerta automática que puede ser abierta
    o cerrada por comandos remotos o en respuesta a eventos del sistema (como detectar
    movimiento cerca de la puerta). El actuador puede publicar su estado en AWS IoT Core.
    """
    
    def __init__(self, id_actuador, ubicacion="Entrada Principal"):
        """Inicializa un nuevo actuador de puerta automática.
        
        Args:
            id_actuador (str): Identificador único del actuador (ej: 'PTA001')
            ubicacion (str): Ubicación física de la puerta (por defecto: 'Entrada Principal')
        """
        self.id_actuador = id_actuador
        self.ubicacion = ubicacion
        self.abierta = False  # Estado inicial: puerta cerrada
        print(f"Actuador de Puerta Automática [{self.id_actuador}] inicializado en: {self.ubicacion}")

    def abrir(self):
        """Abre la puerta automática si no está ya abierta.
        
        Cambia el estado de la puerta a abierta y muestra un mensaje de confirmación.
        Si la puerta ya estaba abierta, simplemente muestra un mensaje informativo.
        """
        if not self.abierta:
            self.abierta = True
            print(f"Actuador Puerta Automática [{self.id_actuador}] ({self.ubicacion}): ABRIENDO...")
        else:
            print(f"Actuador Puerta Automática [{self.id_actuador}] ({self.ubicacion}): ya está abierta.")

    def cerrar(self):
        """Cierra la puerta automática si está abierta.
        
        Cambia el estado de la puerta a cerrada y muestra un mensaje de confirmación.
        Si la puerta ya estaba cerrada, simplemente muestra un mensaje informativo.
        """
        if self.abierta:
            self.abierta = False
            print(f"Actuador Puerta Automática [{self.id_actuador}] ({self.ubicacion}): CERRANDO...")
        else:
            print(f"Actuador Puerta Automática [{self.id_actuador}] ({self.ubicacion}): ya está cerrada.")

    def obtener_estado_str(self):
        """Obtiene una representación en texto del estado actual de la puerta.
        
        Returns:
            str: Cadena de texto describiendo el estado actual de la puerta (ABIERTA/CERRADA),
                 incluyendo su ID y ubicación.
        """
        estado = "ABIERTA" if self.abierta else "CERRADA"
        return f"Actuador P.Automática [{self.id_actuador}] ({self.ubicacion}): {estado}"
        
    def publicar_en_aws_iot(self):
        """Publica el estado del actuador de puerta en AWS IoT Core mediante MQTT.
        
        Utiliza el script pub.py para enviar el estado actual de la puerta automática
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
            "sensor": f"puerta_{self.id_actuador}",     # Identificador único
            "value": 1 if self.abierta else 0,        # 1=abierta, 0=cerrada
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
            "--client_id", f"actuador_puerta_{self.id_actuador}",   # ID de cliente MQTT 
            "--topic", f"data/retail/actuadores/puerta/{self.id_actuador}",  # Tópico MQTT
            "--count", "1",                            # Envío único (no continuo)
            "--message", json.dumps(mensaje)            # Mensaje serializado como JSON
        ]
        
        # Ejecutar el comando y capturar su resultado
        print(f"Publicando estado del actuador de puerta {self.id_actuador}: {'Abierta' if self.abierta else 'Cerrada'}")
        resultado = subprocess.run(comando, cwd=base_path)
        
        # Devolver True si el comando se ejecutó correctamente (código de salida 0)
        return resultado.returncode == 0

# ========================================================================
# Bloque principal para ejecución independiente del actuador de puerta
# ========================================================================

if __name__ == "__main__":
    """Punto de entrada principal cuando se ejecuta este script directamente.
    
    Este bloque permite ejecutar el simulador de puerta automática de forma independiente.
    Crea una instancia del actuador y realiza ciclos de simulación, abriendo y cerrando
    la puerta según patrones temporales que simulan la detección de movimiento en la entrada.
    """
    # Inicializar un actuador de puerta con ID PTA001 ubicado en la entrada de la tienda
    puerta = ActuadorPuertaAutomatica("PTA001", "Entrada Tienda")
    
    try:
        # Iniciar ciclo de simulación
        ciclo = 0
        while True:
            ciclo += 1
            print(f"--- Ciclo {ciclo} ---")
            
            # Cada 3 ciclos: simular detección de movimiento y abrir la puerta
            if ciclo % 3 == 0:
                print("\nEVENTO: Detectando movimiento en entrada, abriendo puerta")
                puerta.abrir()
            
            # Cada 4 ciclos: simular ausencia de movimiento y cerrar la puerta
            if ciclo % 4 == 0:
                print("\nEVENTO: Sin movimiento en entrada, cerrando puerta")
                puerta.cerrar()
            
            # Mostrar el estado actual y publicarlo en AWS IoT Core
            print(puerta.obtener_estado_str())
            exito = puerta.publicar_en_aws_iot()
            
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
