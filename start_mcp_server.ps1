# start_mcp_server.ps1
# Arranca el MCP server en modo HTTP/SSE y lo reinicia si cae.
# Ejecutar una vez en una terminal; dejar corriendo mientras se trabaja.
# El server queda en http://localhost:8001/sse

$python  = "D:\projects\euyin-agent\.venv\Scripts\python.exe"
$script  = "D:\projects\euyin-agent\mcp_server\server.py"
$logFile = "D:\projects\euyin-agent\mcp_server.log"

# Env vars — deben estar antes de que Python importe FastMCP
$env:ABU_ENGINE_URL    = "https://abu-engine-bbrsyawaca-uc.a.run.app"
$env:ABU_DOCTRINE_ROOT = "D:/projects/ai-oracle"
$env:MCP_TRANSPORT     = "sse"
$env:FASTMCP_PORT      = "8001"

Write-Host "Abu Oracle MCP server → http://localhost:$port/sse"
Write-Host "Log: $logFile  |  Ctrl+C para detener`n"

while ($true) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $logFile "[$ts] Iniciando server.py --sse $port"
    Write-Host "[$ts] Iniciando..."

    & $python $script 2>&1 | Tee-Object -Append -FilePath $logFile

    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $logFile "[$ts] Proceso terminado — reiniciando en 2s"
    Write-Host "[$ts] Terminó — reiniciando en 2s..."
    Start-Sleep 2
}
