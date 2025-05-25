import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno para configuración de la base de datos
load_dotenv()

# Configuración de la conexión a PostgreSQL
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'dbname': os.environ.get('DB_NAME', 'retail_iot'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'port': os.environ.get('DB_PORT', '5432')
}

def get_db_connection():
    """Establece y retorna una conexión a la base de datos PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise

def get_all_sensors():
    """Obtiene todos los sensores de la base de datos"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM sensors ORDER BY created_at DESC")
            return cur.fetchall()
    finally:
        conn.close()

def get_sensor_by_id(sensor_id):
    """Obtiene un sensor específico por su ID"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM sensors WHERE sensor_id = %s", (sensor_id,))
            return cur.fetchone()
    finally:
        conn.close()

def create_sensor(sensor_id, name, type, location, status='active'):
    """Crea un nuevo sensor en la base de datos"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            now = datetime.now()
            cur.execute(
                """
                INSERT INTO sensors (sensor_id, name, type, location, created_at, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (sensor_id, name, type, location, now, status)
            )
            conn.commit()
            return cur.fetchone()
    finally:
        conn.close()

def get_sensor_events(sensor_id, limit=100, start_date=None, end_date=None):
    """Obtiene los eventos de un sensor específico con filtros opcionales"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            query = """
                SELECT * FROM events 
                WHERE device_id = %s AND device_type = 'sensor'
            """
            params = [sensor_id]
            
            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)
                
            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)
                
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()

def get_all_actuators():
    """Obtiene todos los actuadores de la base de datos"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM actuators ORDER BY created_at DESC")
            return cur.fetchall()
    finally:
        conn.close()

def create_actuator(actuator_id, name, type, location, status='active'):
    """Crea un nuevo actuador en la base de datos"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            now = datetime.now()
            cur.execute(
                """
                INSERT INTO actuators (actuator_id, name, type, location, created_at, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (actuator_id, name, type, location, now, status)
            )
            conn.commit()
            return cur.fetchone()
    finally:
        conn.close()

def save_event(device_id, device_type, value, unit, timestamp=None, metadata=None):
    """Guarda un nuevo evento en la base de datos"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if timestamp is None:
                timestamp = datetime.now()
                
            if metadata is None:
                metadata = {}
                
            cur.execute(
                """
                INSERT INTO events (device_id, device_type, value, unit, timestamp, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (device_id, device_type, value, unit, timestamp, json.dumps(metadata))
            )
            conn.commit()
            return cur.fetchone()
    finally:
        conn.close()
