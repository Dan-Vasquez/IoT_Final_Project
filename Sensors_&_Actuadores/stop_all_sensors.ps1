# Script para detener todos los sensores y actuadores
Write-Host "Deteniendo todos los sensores y actuadores..."

# Detener todos los procesos de Python que están ejecutando los sensores y actuadores
$procesos = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like '*sensor_movimiento.py*' -or 
    $_.CommandLine -like '*sensor_apertura.py*' -or 
    $_.CommandLine -like '*etiqueta_rfid.py*' -or 
    $_.CommandLine -like '*actuador_alarma.py*' -or 
    $_.CommandLine -like '*actuador_puerta.py*'
}

if ($procesos) {
    foreach ($proceso in $procesos) {
        try {
            Write-Host "Deteniendo proceso: $($proceso.Id)"
            Stop-Process -Id $proceso.Id -Force
        } catch {
            Write-Host "Error al detener proceso $($proceso.Id): $_"
        }
    }
    
    Write-Host "Todos los sensores y actuadores han sido detenidos."
} else {
    Write-Host "No se encontraron procesos de sensores o actuadores en ejecución."
}
