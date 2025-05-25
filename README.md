# Proyecto Final IoT - Sensores y Actuadores Retail con AWS IoT Core

Autores:

- Juan Esteban Becerra

- Daniel Vasquez

## Descripción

Este proyecto implementa un sistema de monitoreo para entornos retail utilizando AWS IoT Core. Los sensores simulados (movimiento, apertura, RFID) y actuadores (alarma, puerta automática) publican datos a través de MQTT en AWS IoT Core siguiendo un formato estandarizado.

## Requisitos

- Python 3.6 o superior
- AWS IoT Core (cuenta con permisos adecuados)
- AWS SDK para Python (boto3, awscrt)
- Certificados AWS IoT (incluidos en carpeta gatewayPUJC)

## Configuración Inicial

Cada vez que se quiera ejecutar scripts PowerShell (.ps1), se debe ejecutar el siguiente comando:
```
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

## Estructura del Proyecto

```
ProyectoFinal-IoT/
├── gatewayPUJC/                # Gateway y configuración AWS IoT
│   ├── Gateway/             # Scripts de publicación/suscripción
│   ├── root-CA.crt           # Certificados AWS IoT
│   ├── *.pem                 # Certificados y claves
│   ├── start.ps1             # Script para publicar
│   └── start_sub.ps1         # Script para suscribirse
├── Sensors_&_Actuadores/     # Implementación de sensores y actuadores
│   ├── sensor_movimiento.py  # Sensor de movimiento
│   ├── sensor_apertura.py    # Sensor de apertura
│   ├── etiqueta_rfid.py      # Etiquetas RFID
│   ├── actuador_alarma.py    # Actuador de alarma
│   ├── actuador_puerta.py    # Actuador de puerta automática
│   ├── start_all_sensors.ps1 # Inicia todos los sensores
│   └── stop_all_sensors.ps1  # Detiene todos los sensores
└── README.md               # Este archivo
```

## Uso del Sistema

### Iniciar los Sensores y Actuadores

```powershell
cd '.\Sensors_&_Actuadores\'
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\start_all_sensors.ps1
```

### Monitorear los Mensajes MQTT

```powershell
cd .\gatewayPUJC\
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\start_sub.ps1
```

### Detener los Sensores y Actuadores

```powershell
cd '.\Sensors_&_Actuadores\'
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\stop_all_sensors.ps1
```

## Estructura de Tópicos MQTT

El proyecto utiliza la siguiente estructura de tópicos MQTT:

```
data/retail/sensors/{tipo_sensor}/{id_sensor}
data/retail/actuadores/{tipo_actuador}/{id_actuador}
```

## Formato de Mensajes

Todos los dispositivos publican mensajes con esta estructura:

```json
{
  "sensor": "nombre_sensor",
  "value": valor_numerico,
  "unit": "unidad_medida",
  "timestamp": "2025-05-24T23:45:00Z",
  ...campos_adicionales_especificos
}
```

## Base de Datos PostgreSQL

El sistema utiliza una base de datos PostgreSQL alojada en una instancia EC2 de AWS para almacenar los datos de sensores, actuadores y eventos. La estructura de la base de datos es la siguiente:

### Tablas de la Base de Datos

#### Tabla `sensors`

| Columna      | Tipo          | Descripción                             |
|--------------|---------------|-----------------------------------------|
| sensor_id    | VARCHAR(50)   | Identificador único del sensor (PK)     |
| name         | VARCHAR(100)  | Nombre descriptivo del sensor           |
| type         | VARCHAR(50)   | Tipo de sensor (movimiento, apertura, rfid) |
| location     | VARCHAR(100)  | Ubicación del sensor                    |
| created_at   | TIMESTAMP     | Fecha de creación del registro          |
| status       | VARCHAR(20)   | Estado del sensor (activo/inactivo)     |

#### Tabla `actuators`

| Columna      | Tipo          | Descripción                             |
|--------------|---------------|-----------------------------------------|
| actuator_id  | VARCHAR(50)   | Identificador único del actuador (PK)   |
| name         | VARCHAR(100)  | Nombre descriptivo del actuador         |
| type         | VARCHAR(50)   | Tipo de actuador (alarma, puerta)       |
| location     | VARCHAR(100)  | Ubicación del actuador                  |
| created_at   | TIMESTAMP     | Fecha de creación del registro          |
| status       | VARCHAR(20)   | Estado del actuador (activo/inactivo)   |

#### Tabla `events`

| Columna      | Tipo          | Descripción                             |
|--------------|---------------|-----------------------------------------|
| event_id     | SERIAL        | Identificador único del evento (PK)     |
| device_id    | VARCHAR(50)   | ID del sensor o actuador                |
| device_type  | VARCHAR(10)   | Tipo de dispositivo (sensor/actuador)   |
| value        | FLOAT         | Valor registrado                        |
| unit         | VARCHAR(20)   | Unidad de medida                        |
| timestamp    | TIMESTAMP     | Fecha y hora del evento                 |
| metadata     | JSONB         | Datos adicionales en formato JSON       |

## API REST con AWS Chalice

El proyecto incluye una API REST desarrollada con AWS Chalice que se comunica con la base de datos PostgreSQL para gestionar sensores, actuadores y eventos.

### Endpoints de la API

| Método | Ruta                         | Funcionalidad                 |
| ------ | ---------------------------- | ----------------------------- |
| GET    | /sensors                     | Listar sensores registrados   |
| POST   | /sensors                     | Registrar un nuevo sensor     |
| GET    | /sensors/{sensor_id}/events  | Ver eventos de un sensor      |
| GET    | /actuators                   | Listar actuadores registrados |
| POST   | /actuators                   | Registrar un nuevo actuador   |

### Estructura de la Carpeta API

```
ProyectoFinal-IoT/
├── api/                      # Carpeta de la API con Chalice
│   ├── app.py                # Aplicación principal de Chalice
│   ├── chalicelib/           # Biblioteca de funciones auxiliares
│   │   ├── __init__.py       
│   │   ├── db.py             # Funciones de acceso a la base de datos
│   │   └── utils.py          # Utilidades generales
│   ├── .chalice/            # Configuración de Chalice
│   └── requirements.txt      # Dependencias de la API
```

### Configuración de la instancia EC2 con PostgreSQL

La base de datos PostgreSQL se ejecuta en una instancia EC2 configurada con un script de inicialización (user-data). Los datos de conexión se gestionan de forma segura mediante variables de entorno en la configuración de Chalice.

## Licencia

Este proyecto está bajo la **Licencia MIT** - ver el archivo [LICENSE](LICENSE) para más detalles.
