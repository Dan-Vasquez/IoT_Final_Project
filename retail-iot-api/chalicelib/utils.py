############################################################
# Módulo de Utilidades para IoT Retail API              #
# Proporciona funciones auxiliares para el procesamiento   #
# de datos de dispositivos IoT y mensajes MQTT            #
############################################################

import json            # Para serialización/deserialización de datos JSON
import datetime        # Para manejo de fechas y horas
from typing import Dict, Any, Union  # Para anotaciones de tipo

def parse_timestamp(timestamp_str: str) -> datetime.datetime:
    """
    Convierte una cadena de timestamp ISO 8601 a un objeto datetime de Python.
    
    Esta función maneja el formato estándar ISO 8601 para fechas y horas, incluido
    el manejo de la zona UTC (indicada por 'Z'). Reemplaza 'Z' por '+00:00' para
    compatibilidad con el método fromisoformat de Python.
    
    Args:
        timestamp_str (str): String en formato ISO 8601, ej: '2023-05-29T14:30:15Z'
        
    Returns:
        datetime.datetime: Objeto datetime de Python equivalente
        
    Raises:
        ValueError: Si el formato del timestamp no es válido o no se puede convertir
        
    Example:
        >>> parse_timestamp('2023-05-29T14:30:15Z')
        datetime.datetime(2023, 5, 29, 14, 30, 15, tzinfo=datetime.timezone.utc)
    """
    try:
        # Convertir 'Z' (que indica UTC) a '+00:00' para compatibilidad con fromisoformat
        return datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        # Capturar y relanzar errores con mensaje más descriptivo
        raise ValueError(f"Formato de timestamp inválido: {timestamp_str}")

def format_timestamp(dt: datetime.datetime) -> str:
    """
    Convierte un objeto datetime de Python a una cadena en formato ISO 8601.
    
    Esta función realiza la operación inversa a parse_timestamp, convirtiendo
    un objeto datetime a una cadena de texto ISO 8601 con zona horaria UTC ('Z').
    Reemplaza '+00:00' por 'Z' para cumplir con las convenciones estándar de IoT.
    
    Args:
        dt (datetime.datetime): Objeto datetime de Python a convertir
        
    Returns:
        str: Cadena en formato ISO 8601 con 'Z' indicando UTC,
             ej: '2023-05-29T14:30:15Z'
             
    Example:
        >>> format_timestamp(datetime.datetime(2023, 5, 29, 14, 30, 15, tzinfo=datetime.timezone.utc))
        '2023-05-29T14:30:15Z'
    """
    # Convertir a ISO 8601 y reemplazar '+00:00' (formato Python) por 'Z' (formato estándar)
    return dt.isoformat().replace('+00:00', 'Z')

def validate_json_payload(payload: Dict[str, Any], required_fields: list) -> bool:
    """
    Valida que un payload JSON contenga todos los campos requeridos.
    
    Esta función verifica que un diccionario JSON contenga todas las claves especificadas
    en la lista de campos requeridos. Se utiliza para validar entradas de API y mensajes MQTT
    antes de procesarlos, garantizando que contengan toda la información necesaria.
    
    Args:
        payload (Dict[str, Any]): Diccionario que representa el payload JSON a validar
        required_fields (list): Lista de nombres de campos (strings) que deben estar presentes
        
    Returns:
        bool: True si todos los campos requeridos están presentes, False en caso contrario
        
    Example:
        >>> data = {'sensor': 'temperatura_001', 'value': 25.5, 'unit': 'C'}
        >>> validate_json_payload(data, ['sensor', 'value', 'unit'])
        True
        >>> validate_json_payload(data, ['sensor', 'value', 'unit', 'timestamp'])
        False
    """
    # Verificar que todos los campos de required_fields estén en el payload
    return all(field in payload for field in required_fields)

def parse_mqtt_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa un mensaje MQTT para extraer y estructurar los datos relevantes para el sistema IoT.
    
    Esta función analiza un mensaje MQTT recibido de dispositivos IoT y lo transforma
    en un formato estandarizado para su procesamiento en la aplicación. Realiza las
    siguientes operaciones:
    
    1. Valida que el mensaje contenga los campos obligatorios
    2. Extrae el tipo de dispositivo y su ID del campo 'sensor'
    3. Clasifica automáticamente si es un sensor o actuador
    4. Convierte el timestamp a un objeto datetime
    5. Agrega cualquier campo adicional como metadata
    
    Args:
        message (Dict[str, Any]): Diccionario que representa el mensaje MQTT recibido,
                                  debe contener al menos los campos requeridos
        
    Returns:
        Dict[str, Any]: Diccionario estandarizado con los datos estructurados:
                        - device_id: ID único del dispositivo
                        - device_type: 'sensor' o 'actuator'
                        - value: Valor registrado
                        - unit: Unidad de medida
                        - timestamp: Objeto datetime del evento
                        - metadata: Diccionario con campos adicionales
                        
    Raises:
        ValueError: Si el mensaje no tiene el formato esperado o faltan campos requeridos
        
    Example:
        >>> msg = {
        ...     'sensor': 'temperatura_TEMP001',
        ...     'value': 25.5,
        ...     'unit': 'C',
        ...     'timestamp': '2023-05-29T14:30:15Z',
        ...     'area': 'Almacén Principal'
        ... }
        >>> parse_mqtt_message(msg)
        {
            'device_id': 'TEMP001',
            'device_type': 'sensor',
            'value': 25.5,
            'unit': 'C',
            'timestamp': datetime.datetime(2023, 5, 29, 14, 30, 15, tzinfo=datetime.timezone.utc),
            'metadata': {'area': 'Almacén Principal'}
        }
    """
    # Validar formato básico del mensaje - debe contener campos obligatorios
    required_fields = ['sensor', 'value', 'unit', 'timestamp']
    if not validate_json_payload(message, required_fields):
        raise ValueError("Mensaje MQTT con formato inválido")
    
    # Extraer tipo y ID del sensor del campo 'sensor' (formato: tipo_id)
    sensor_parts = message['sensor'].split('_')
    if len(sensor_parts) != 2:
        raise ValueError(f"Formato de sensor inválido: {message['sensor']}")
    
    device_type, device_id = sensor_parts
    
    # Determinar si es sensor o actuador basado en el tipo de dispositivo
    # Los dispositivos de tipo 'alarma' o 'puerta' se consideran actuadores
    is_actuator = device_type in ['alarma', 'puerta']
    
    # Estructurar los datos en formato estandarizado
    parsed_data = {
        'device_id': device_id,                            # ID único del dispositivo
        'device_type': 'actuator' if is_actuator else 'sensor',  # Clasificación del dispositivo
        'value': message['value'],                         # Valor registrado
        'unit': message['unit'],                           # Unidad de medida
        'timestamp': parse_timestamp(message['timestamp']),  # Convertir a objeto datetime
        'metadata': {}                                     # Inicializar metadata vacía
    }
    
    # Añadir campos adicionales como metadata (cualquier campo no estándar)
    for key, value in message.items():
        if key not in required_fields:
            parsed_data['metadata'][key] = value
    
    return parsed_data
