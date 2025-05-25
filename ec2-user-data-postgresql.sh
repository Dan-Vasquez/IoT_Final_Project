#!/bin/bash
# User data script to install and configure PostgreSQL on an EC2 instance

# it’s essential to update your system to ensure you have the latest updates and refresh the DNF package cache.
sudo dnf update -y

# Installa PostgreSQL
sudo dnf install postgresql15.x86_64 postgresql15-server -y

# Initializing PostgreSQL Database
sudo postgresql-setup --initdb

# Starting and Enabling PostgreSQL Service
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl status postgresql

# Configure PostgreSQL
# Set password for ssh postgres user and admin postgres database password
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'YourNewPassword';"

# Primary Configuration File
sudo cp /var/lib/pgsql/data/postgresql.conf /var/lib/pgsql/data/postgresql.conf.bck

# Optionally, configure PostgreSQL to listen on all interfaces.
#  -  **WARNING:**  This makes your database accessible from anywhere, which can be a security risk.
#  -  Only enable this if you understand the security implications and have appropriate firewall rules in place.
#  -  This is often NOT necessary and is discouraged for production environments.
#  -  If you need remote access, consider using an SSH tunnel instead.
echo "listen_addresses = '*'" | sudo tee -a /var/lib/pgsql/data/postgresql.conf


# Next, you need to configure the pg_hba.conf file to allow connections from your remote EC2 instance. Open the pg_hba.conf file
sudo cp /var/lib/pgsql/data/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf.bck

#Add an entry at the end of the file to allow connections from your remote EC2 instance
echo "host    all             all             0.0.0.0/0            md5" | sudo tee -a /var/lib/pgsql/data/pg_hba.conf

# To apply all the changes, restart the PostgreSQL service using the following command.
sudo systemctl restart postgresql

# Optionally, create a new database and user
#  -  Replace 'your_database_name' and 'your_user_name' with your desired names.
#  -  Replace 'YourNewPassword' with a strong, secure password.
#  -  This is just an example; adapt it to your specific needs.
sudo -u postgres psql -c "CREATE DATABASE iot_final_project;"
sudo -u postgres psql -c "CREATE USER dok WITH PASSWORD 'dok';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE iot_final_project TO dok;"

echo "PostgreSQL installation complete."


