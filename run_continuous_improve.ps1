$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
  Write-Error "未找到虚拟环境 Python：$python"
  exit 1
}

& $python "$PSScriptRoot\continuous_improve.py"
