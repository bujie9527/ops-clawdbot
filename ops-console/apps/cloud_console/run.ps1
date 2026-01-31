# 在 cloud_console 目录下运行：.\run.ps1
# 若没有 .venv 会先创建并安装依赖，再启动 uvicorn（无需手动 activate）
# 启动前会先清理占用 8000 端口的进程，避免重复启动导致连接卡住

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

# 清理占用 8000 端口的进程
$pids = netstat -ano | Select-String ":8000\s+.*LISTENING" | ForEach-Object {
    if ($_.Line -match "\s+(\d+)\s*$") { $matches[1] }
} | Sort-Object -Unique
if ($pids) {
    Write-Host "Killing processes on port 8000: $($pids -join ', ')"
    foreach ($pid in $pids) {
        try { taskkill /F /PID $pid 2>$null } catch { }
    }
    Start-Sleep -Seconds 2
}

$venv = Join-Path $root ".venv"
$py = Join-Path $venv "Scripts\python.exe"
$uvicorn = Join-Path $venv "Scripts\uvicorn.exe"

if (-not (Test-Path $py)) {
    Write-Host "Creating .venv ..."
    python -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "venv creation failed" }
    & $py -m pip install -r requirements.txt -q
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
}

if (-not (Test-Path $uvicorn)) {
    & $py -m pip install -r requirements.txt -q
}

Write-Host "Starting uvicorn (http://localhost:8000) ..."
& $py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
