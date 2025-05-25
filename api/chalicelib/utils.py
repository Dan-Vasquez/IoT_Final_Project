import json
import datetime
from typing import Dict, Any, Union

def parse_timestamp(timestamp_str: str) -> datetime.datetime:
    """
    Convierte una cadena de timestamp ISO 8601 a un objeto datetime.
    
    Args:
        timestamp_str: String en formato ISO 8601
        
    Returns:
        Objeto datetime
    """
    try:
        return datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        raise ValueError(f"Formato de timestamp inválido: {timestamp_str}")

def format_timestamp(dt: datetime.datetime) -> str:
    """
    Convierte un objeto datetime a un string ISO 8601.
    
    Args:
        dt: Objeto datetime
        
    Returns:
        String en formato ISO 8601
    """
    return dt.isoformat().replace('+00:00', 'Z')

def validate_json_payload(payload: Dict[str, Any], required_fields: list) -> bool:
    """
    Valida que un payload JSON contenga todos los campos requeridos.
    
    Args:
        payload: Diccionario que representa el payload JSON
        required_fields: Lista de campos requeridos
        
    Returns:
        True si todos los campos están presentes, False en caso contrario
    """
    return all(field in payload for field in required_fields)

def parse_mqtt_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa un mensaje MQTT para extraer y estructurar los datos relevantes.
    
    Args:
        message: Diccionario que representa el mensaje MQTT
        
    Returns:
        Diccionario con los datos estructurados
    """
    # Validar formato básico del mensaje
    required_fields = ['sensor', 'value', 'unit', 'timestamp']
    if not validate_json_payload(message, required_fields):
        raise ValueError("Mensaje MQTT con formato inválido")
    
    # Extraer tipo y ID del sensor del campo 'sensor'
    sensor_parts = message['sensor'].split('_')
    if len(sensor_parts) != 2:
        raise ValueError(f"Formato de sensor inválido: {message['sensor']}")
    
    device_type, device_id = sensor_parts
    
    # Determinar si es sensor o actuador
    is_actuator = device_type in ['alarma', 'puerta']
    
    # Estructurar los datos
    parsed_data = {
        'device_id': device_id,
        'device_type': 'actuator' if is_actuator else 'sensor',
        'value': message['value'],
        'unit': message['unit'],
        'timestamp': parse_timestamp(message['timestamp']),
        'metadata': {}
    }
    
    # Añadir campos adicionales como metadata
    for key, value in message.items():
        if key not in required_fields:
            parsed_data['metadata'][key] = value
    
    return parsed_data
