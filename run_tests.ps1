$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
$staticDir = Join-Path $repoRoot 'static'

$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
if ($npmCommand) {
    $npm = $npmCommand.Source
}
else {
    $candidateRoots = @(
        (Join-Path $env:ProgramFiles 'nodejs\npm.cmd'),
        (Join-Path ${env:ProgramFiles(x86)} 'nodejs\npm.cmd'),
        'D:\software\npm.cmd',
        'D:\软件\npm.cmd'
    )
    $npm = $candidateRoots | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
    if (-not $npm) {
        $npm = Get-ChildItem -Path 'D:\' -Filter 'npm.cmd' -File -Recurse -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty FullName
    }
}

if (-not (Test-Path $python)) {
    throw "Virtual environment Python not found: $python"
}

if (-not $npm) {
    throw 'npm.cmd not found. Add Node.js to PATH or update run_tests.ps1 with the local npm.cmd path.'
}

$npmDir = Split-Path -Parent $npm
if ($npmDir -and -not ($env:Path -split ';' | Where-Object { $_ -eq $npmDir })) {
    $env:Path = $npmDir + ';' + $env:Path
}

Write-Host '== Backend API tests ==' -ForegroundColor Cyan
& $python -m pytest `
    "$repoRoot\tests\test_heat3d_api.py" `
    "$repoRoot\tests\test_poisson3d_api.py" `
    "$repoRoot\tests\test_wave3d_api.py" `
    "$repoRoot\tests\test_websocket_api.py" `
    -q

Write-Host '== Frontend SolvePage test ==' -ForegroundColor Cyan
Push-Location $staticDir
try {
    & $npm run test -- --run SolvePage

    Write-Host '== Frontend build ==' -ForegroundColor Cyan
    & $npm run build
}
finally {
    Pop-Location
}
