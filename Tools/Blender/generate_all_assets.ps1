param(
    [string]$BlenderExe = "blender"
)

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$scriptDirectory = Join-Path $projectRoot "Tools\Blender"
$generators = Get-ChildItem -LiteralPath $scriptDirectory -Filter "create_*.py" | Sort-Object Name

foreach ($generator in $generators) {
    Write-Host "Generating $($generator.BaseName)..."
    & $BlenderExe --background --python-exit-code 1 --python $generator.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Blender failed while running $($generator.Name) (exit code $LASTEXITCODE)."
    }
}

Write-Host "All active Blender asset generators completed."
