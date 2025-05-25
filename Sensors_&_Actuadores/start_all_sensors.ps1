# Script maestro para iniciar todos los sensores y actuadores
Write-Host "Iniciando todos los sensores y actuadores para el proyecto de Retail IoT..."
Write-Host "----------------------------------------------------------------"

# Obtener el directorio base
$baseDir = $PSScriptRoot

# Definir la versión de Python que funciona con el SDK de AWS IoT
$pythonCommand = "python"

# Iniciar sensor de movimiento en segundo plano
Write-Host "Iniciando sensores de movimiento..."
Start-Process -FilePath $pythonCommand -ArgumentList "$baseDir\sensor_movimiento.py" -NoNewWindow

# Iniciar sensor de apertura en segundo plano
Write-Host "Iniciando sensores de apertura..."
Start-Process -FilePath $pythonCommand -ArgumentList "$baseDir\sensor_apertura.py" -NoNewWindow

# Iniciar etiqueta RFID en segundo plano
Write-Host "Iniciando etiquetas RFID..."
Start-Process -FilePath $pythonCommand -ArgumentList "$baseDir\etiqueta_rfid.py" -NoNewWindow

# Iniciar actuador de alarma en segundo plano
Write-Host "Iniciando actuadores de alarma..."
Start-Process -FilePath $pythonCommand -ArgumentList "$baseDir\actuador_alarma.py" -NoNewWindow

# Iniciar actuador de puerta en segundo plano
Write-Host "Iniciando actuadores de puerta..."
Start-Process -FilePath $pythonCommand -ArgumentList "$baseDir\actuador_puerta.py" -NoNewWindow

Write-Host "Todos los sensores y actuadores han sido iniciados en segundo plano!"
Write-Host "Para detenerlos, cierre cada una de las ventanas de terminal o use el script stop_all_sensors.ps1"
