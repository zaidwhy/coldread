# Unattended COLD READ sweep for one Ollama model: pull, sweep, retry failed rows, analyse.
# Needs no Claude session. Run detached, for example:
#   Start-Process powershell -WindowStyle Hidden -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File scripts\run_model_sweep.ps1 -Model mistral:7b'
# Progress: out\run-<model>.log   Result: out\results-<model>.jsonl, out\analysis-<model>.txt
# Final state: out\run-<model>.status holds DONE, FAILED_PULL or INCOMPLETE with a timestamp and row counts.
param(
    [string]$Model = "mistral:7b",
    [int]$ExpectedRows = 504
)

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONIOENCODING = "utf-8"
$slug = $Model.Replace(":", "_")
$log = Join-Path $root "out\run-$slug.log"
$statusFile = Join-Path $root "out\run-$slug.status"
$resultFile = Join-Path $root "out\results-$slug.jsonl"
$noBom = New-Object System.Text.UTF8Encoding($false)

function Log([string]$m) { "$(Get-Date -Format s) $m" | Out-File -Append -Encoding utf8 $log }
function SetStatus([string]$s) { [System.IO.File]::WriteAllText($statusFile, "$s $(Get-Date -Format s)`r`n", $noBom) }

# Keep the machine awake for the whole run (released automatically when this process exits).
Add-Type -Namespace Win32 -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[void][Win32.Power]::SetThreadExecutionState(0x80000001)

Log "start model=$Model"
SetStatus "RUNNING"

$pulled = $false
for ($i = 1; $i -le 6 -and -not $pulled; $i++) {
    Log "pull attempt $i"
    ollama pull $Model 2>&1 | Out-File -Append -Encoding utf8 $log
    if (ollama list | Select-String -SimpleMatch $Model) { $pulled = $true } else { Start-Sleep 30 }
}
if (-not $pulled) { Log "pull failed"; SetStatus "FAILED_PULL"; exit 1 }
Log "model present"

$good = @()
for ($a = 1; $a -le 5; $a++) {
    Log "sweep attempt $a"
    python sweep.py --model $Model 2>&1 | Out-File -Append -Encoding utf8 $log
    if (Test-Path $resultFile) {
        $rows = @(Get-Content $resultFile -Encoding utf8 | Where-Object { $_.Trim() })
        $good = @($rows | Where-Object { $null -eq ($_ | ConvertFrom-Json).error })
        $bad = $rows.Count - $good.Count
        [System.IO.File]::WriteAllLines($resultFile, [string[]]$good, $noBom)
        Log "rows=$($rows.Count) good=$($good.Count) errors_removed_for_retry=$bad"
    }
    if ($good.Count -ge $ExpectedRows) { break }
}

if ($good.Count -lt $ExpectedRows) { Log "incomplete"; SetStatus "INCOMPLETE rows=$($good.Count)/$ExpectedRows"; exit 2 }

python analyze.py $resultFile 2>&1 | Out-File -Encoding utf8 (Join-Path $root "out\analysis-$slug.txt")
ollama stop $Model 2>&1 | Out-Null
Log "done"
SetStatus "DONE rows=$($good.Count)/$ExpectedRows"
