from chalice import Chalice, Response, BadRequestError, NotFoundError
from chalicelib.db import (
    get_all_sensors,
    get_sensor_by_id,
    create_sensor,
    get_sensor_events,
    get_all_actuators,
    create_actuator
)
import os
import json

app = Chalice(app_name='retail-iot-api')

@app.route('/sensors', methods=['GET'])
def list_sensors():
    """Lista todos los sensores registrados"""
    sensors = get_all_sensors()
    return {'sensors': sensors}

@app.route('/sensors', methods=['POST'])
def add_sensor():
    """Registra un nuevo sensor"""
    body = app.current_request.json_body
    required_fields = ['sensor_id', 'name', 'type', 'location']
    
    # Verificar campos requeridos
    for field in required_fields:
        if field not in body:
            raise BadRequestError(f"Campo requerido '{field}' faltante")
    
    try:
        sensor = create_sensor(
            sensor_id=body['sensor_id'],
            name=body['name'],
            type=body['type'],
            location=body['location'],
            status=body.get('status', 'active')
        )
        return {'message': 'Sensor creado exitosamente', 'sensor': sensor}
    except Exception as e:
        raise BadRequestError(f"Error al crear sensor: {str(e)}")

@app.route('/sensors/{sensor_id}/events', methods=['GET'])
def get_events_for_sensor(sensor_id):
    """Obtiene todos los eventos de un sensor específico"""
    # Verificar que el sensor existe
    sensor = get_sensor_by_id(sensor_id)
    if not sensor:
        raise NotFoundError(f"Sensor con ID '{sensor_id}' no encontrado")
    
    # Obtener parámetros de consulta opcionales para filtrado
    params = app.current_request.query_params or {}
    limit = int(params.get('limit', 100))
    start_date = params.get('start_date')
    end_date = params.get('end_date')
    
    events = get_sensor_events(
        sensor_id=sensor_id,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )
    
    return {'sensor_id': sensor_id, 'events': events}

@app.route('/actuators', methods=['GET'])
def list_actuators():
    """Lista todos los actuadores registrados"""
    actuators = get_all_actuators()
    return {'actuators': actuators}

@app.route('/actuators', methods=['POST'])
def add_actuator():
    """Registra un nuevo actuador"""
    body = app.current_request.json_body
    required_fields = ['actuator_id', 'name', 'type', 'location']
    
    # Verificar campos requeridos
    for field in required_fields:
        if field not in body:
            raise BadRequestError(f"Campo requerido '{field}' faltante")
    
    try:
        actuator = create_actuator(
            actuator_id=body['actuator_id'],
            name=body['name'],
            type=body['type'],
            location=body['location'],
            status=body.get('status', 'active')
        )
        return {'message': 'Actuador creado exitosamente', 'actuator': actuator}
    except Exception as e:
        raise BadRequestError(f"Error al crear actuador: {str(e)}")

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar el estado de la API"""
    return {'status': 'healthy'}
