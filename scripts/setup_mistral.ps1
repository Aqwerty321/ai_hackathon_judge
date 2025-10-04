param(
    [string]$PythonPath,
    [string]$DownloadScript = (Join-Path $PSScriptRoot "download_mistral.py")
)

function Write-Step {
    param([string]$Message)
    Write-Host "[setup] $Message" -ForegroundColor Cyan
}

if (-not $PythonPath) {
    $projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
    $defaultPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
    if (Test-Path $defaultPython) {
        $PythonPath = $defaultPython
    } else {
        $PythonPath = "python"
    }
}

if ($PythonPath -ne "python" -and -not (Test-Path $PythonPath)) {
    throw "Python executable not found at '$PythonPath'. Use -PythonPath to point to the correct interpreter."
}

Write-Step "Using Python at $PythonPath"

$packages = @("huggingface_hub", "ctransformers")
foreach ($package in $packages) {
    Write-Step "Installing/updating $package"
    & $PythonPath -m pip install --upgrade $package
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install package '$package'."
    }
}

if (-not (Test-Path $DownloadScript)) {
    throw "Download script not found at '$DownloadScript'."
}

Write-Step "Running Hugging Face download helper"
& $PythonPath $DownloadScript
if ($LASTEXITCODE -ne 0) {
    throw "Model download script exited with code $LASTEXITCODE."
}

Write-Step "Mistral model setup complete."
Write-Host "Model file should now exist at models/mistral-7b-instruct-v0.2.Q4_K_M.gguf" -ForegroundColor Green
