# Stop any process using port 8000
$port = 8000
$procs = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($procs) {
    Write-Host "Stopping process(es) using port $port: $procs"
    foreach ($pid in $procs) { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue }
} else {
    Write-Host "No process found using port $port"
}
