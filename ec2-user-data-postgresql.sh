#!/bin/bash
# User data script to install and configure PostgreSQL on an EC2 instance

# 1. Actualizar sistema
sudo dnf update -y

# 2. Instalar PostgreSQL
sudo dnf install postgresql15.x86_64 postgresql15-server -y

# 3. Inicializar la base de datos
sudo postgresql-setup --initdb

# 4. Iniciar y habilitar servicio
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 5. Configurar contraseña del usuario postgres
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '12345';"

# 6. Permitir conexiones remotas (opcional, ajustar firewall)
sudo cp /var/lib/pgsql/data/postgresql.conf /var/lib/pgsql/data/postgresql.conf.bck
echo "listen_addresses = '*'" | sudo tee -a /var/lib/pgsql/data/postgresql.conf

sudo cp /var/lib/pgsql/data/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf.bck
echo "host    all             all             0.0.0.0/0            md5" | sudo tee -a /var/lib/pgsql/data/pg_hba.conf

sudo systemctl restart postgresql

# 7. Crear base de datos y usuario
sudo -u postgres psql -c "CREATE DATABASE iot_final_project;"
sudo -u postgres psql -c "CREATE USER dok WITH PASSWORD 'dok';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE iot_final_project TO dok;"

# 8. Crear las tablas dentro de iot_final_project
cat <<'EOF' | sudo -u postgres psql -d iot_final_project
-- Tabla de sensores
CREATE TABLE IF NOT EXISTS sensors (
    sensor_id   VARCHAR(50)   PRIMARY KEY,
    name        VARCHAR(100)  NOT NULL,
    type        VARCHAR(50)   NOT NULL,
    location    VARCHAR(100),
    created_at  TIMESTAMP     DEFAULT NOW(),
    status      VARCHAR(20)   DEFAULT 'activo'
);

-- Tabla de actuadores
CREATE TABLE IF NOT EXISTS actuators (
    actuator_id VARCHAR(50)   PRIMARY KEY,
    name        VARCHAR(100)  NOT NULL,
    type        VARCHAR(50)   NOT NULL,
    location    VARCHAR(100),
    created_at  TIMESTAMP     DEFAULT NOW(),
    status      VARCHAR(20)   DEFAULT 'activo'
);

-- Tabla de eventos
CREATE TABLE IF NOT EXISTS events (
    event_id     SERIAL       PRIMARY KEY,
    device_id    VARCHAR(50)  NOT NULL,
    device_type  VARCHAR(10)  NOT NULL,
    value        FLOAT        NOT NULL,
    unit         VARCHAR(20),
    timestamp    TIMESTAMP    NOT NULL,
    metadata     JSONB
);
EOF

echo "PostgreSQL installation and schema setup complete."
