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

$refinementScript = Join-Path $scriptDirectory "refine_asset_models.py"
Write-Host "Applying the shared art direction and rendering updated previews..."
& $BlenderExe --background --python-exit-code 1 --python $refinementScript
if ($LASTEXITCODE -ne 0) {
    throw "Blender failed while refining the generated assets (exit code $LASTEXITCODE)."
}

Write-Host "All Blender asset generators and refinements completed."
