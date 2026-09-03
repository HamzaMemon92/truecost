$ErrorActionPreference = "Stop"
Write-Host "dYs? TRUECOST MOBILE WEB SCRAPER CERTIFICATION PIPELINE" -ForegroundColor Cyan

# Safe finalization vars
$ADB = $null
$emulatorProcess = $null
$backendProcess = $null

$runId = [DateTime]::UtcNow.ToString("yyyyMMdd_HHmmss") + "_" + (Get-Random -Maximum 9999)
Write-Host "dY+ Run ID: $runId"

$report = @{
  status = "BLOCKED"
  run_id = $runId
  captures_expected = 0
  captures_exported = 0
  exact_mapping_verified = $false
  replay_passed = $false
  critical_failures = @()
  blocked_reasons = @()
}

$script:certificationFailed = $false

function Add-CriticalFailure($msg) {
    $script:certificationFailed = $true
    $report.critical_failures += $msg
    Write-Host "?O $msg" -ForegroundColor Red
}

function Add-BlockedReason($msg) {
    $report.blocked_reasons += $msg
    Write-Host "s,? $msg" -ForegroundColor Yellow
}

try {
    # 1. Resolve App ID
    $APP_ID = $env:TRUECOST_APP_ID
    if (-not $APP_ID) {
        if (Test-Path "mobile/app.json") {
            $appJson = Get-Content "mobile/app.json" | ConvertFrom-Json
            $APP_ID = $appJson.expo.android.package
        }
        if (-not $APP_ID) {
            Add-CriticalFailure "Could not resolve APP_ID"
        }
    }

    # 2. Verify Java
    try {
        java -version 2>&1 | Out-Null
    } catch {
        Add-BlockedReason "Java not found in PATH"
        exit 1
    }

    # 3. Verify Maestro
    try {
        maestro --version 2>&1 | Out-Null
    } catch {
        Add-BlockedReason "Maestro not found"
        exit 1
    }

    # Verify Android SDK
    $SDK = $env:ANDROID_HOME
    if (-not $SDK) {
        Add-BlockedReason "ANDROID_HOME not set"
        exit 1
    }
    $ADB = "$SDK\platform-tools\adb.exe"
    $EMULATOR = "$SDK\emulator\emulator.exe"

    Write-Host "? Starting AVD..."
    # Resolve AVD: prefer env var, then discover first available AVD
    $avdName = $env:TRUECOST_ANDROID_AVD_NAME
    if (-not $avdName) {
        $avdList = & $EMULATOR -list-avds 2>&1 | Where-Object { $_ -and $_.Trim() -ne "" }
        if ($avdList) {
            $avdName = ($avdList | Select-Object -First 1).Trim()
            Write-Host "Auto-selected AVD: $avdName" -ForegroundColor Yellow
        }
    }
    if (-not $avdName) {
        Add-BlockedReason "BLOCKED_AVD_REQUIRED: No AVD found. Set TRUECOST_ANDROID_AVD_NAME or create an AVD first."
        exit 1
    }
    $emulatorProcess = Start-Process -FilePath $EMULATOR -ArgumentList "-avd", $avdName -PassThru -NoNewWindow


    Write-Host "dY"? Waiting for Android boot..."
    & $ADB wait-for-device
    $booted = $false
    for ($i=0; $i -lt 60; $i++) {
        $out = & $ADB shell getprop sys.boot_completed
        if ($out -match "1") { $booted = $true; break }
        Start-Sleep -Seconds 2
    }
    if (-not $booted) { Add-CriticalFailure "Emulator failed to boot." }

    Write-Host "dY"? Starting Backend..."
    Set-Location backend
    $backendProcess = Start-Process -FilePath "uvicorn" -ArgumentList "app.main:app", "--port", "8000" -PassThru -NoNewWindow
    Set-Location ..

    Write-Host "dY"? Waiting for Backend Health..."
    $health = $false
    for ($i=0; $i -lt 30; $i++) {
        try {
            $res = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -Method Get -ErrorAction Stop
            if ($res.StatusCode -eq 200) { $health = $true; break }
        } catch {}
        Start-Sleep -Seconds 1
    }
    if (-not $health) { Add-CriticalFailure "Backend health check failed." }

    Write-Host "dY"? Building/Installing TrueCost..."
    $env:EXPO_PUBLIC_CERT_BACKEND_URL = "http://10.0.2.2:8000"
    Set-Location mobile
    npx expo run:android
    if ($LASTEXITCODE -ne 0) { Add-CriticalFailure "npx expo run:android failed." }
    Set-Location ..

    $checkApp = & $ADB shell pm list packages | Select-String $APP_ID
    if (-not $checkApp) { Add-CriticalFailure "App installation verification failed." }

    Write-Host "dY"? Syncing Case Source..."
    $casesJson = Get-Content "certification/cases.json" -Encoding UTF8 | ConvertFrom-Json
    $expectedCaseIds = $casesJson.case_id
    $report.captures_expected = $expectedCaseIds.Count

    Write-Host "dY"? Running Maestro Tests..."
    Set-Location mobile
    try {
        foreach ($case in $casesJson) {
            $encQuery = [System.Uri]::EscapeDataString($case.query)
            $deepLink = "truecost://scraper_cert?provider=$($case.provider)&caseId=$($case.case_id)&domain=$($case.domain)&query=$encQuery&runId=$runId"
            Write-Host "Running Maestro for $($case.case_id)..."
            maestro test .maestro/scraper-certification/scrape-provider-case.yaml -e TRUECOST_APP_ID=$APP_ID -e RUN_ID=$runId -e DEEP_LINK="$deepLink"
            if ($LASTEXITCODE -ne 0) {
                Add-CriticalFailure "Maestro test failed for $($case.case_id)"
            }
        }
    } catch {
        Add-CriticalFailure "Maestro failed to execute: $_"
    }
    Set-Location ..

    Write-Host "dY"? Exporting Captures via ADB..."
    $exportDir = "backend/tests/fixtures/scraper_certification/runs/$runId"
    New-Item -ItemType Directory -Path $exportDir -Force | Out-Null
    
    $deviceDir = "files/scraper_captures/$runId"
    $checkAccess = & $ADB shell run-as $APP_ID ls $deviceDir 2>&1
    if ($LASTEXITCODE -ne 0) {
        Add-CriticalFailure "CAPTURE_EXPORT_BLOCKED: App directory not accessible via run-as."
    } else {
        & $ADB exec-out run-as $APP_ID sh -c "tar -cf - -C $deviceDir ." > captures.tar
        if ($LASTEXITCODE -eq 0 -and (Get-Item captures.tar).Length -gt 0) {
            tar -xf captures.tar -C $exportDir
            Write-Host "✅ Captures exported successfully via tar." -ForegroundColor Green
        } else {
            $files = & $ADB shell run-as $APP_ID ls $deviceDir
            foreach ($file in ($files -split '\s+' | Where-Object { $_ -ne '' })) {
                & $ADB exec-out run-as $APP_ID cat $deviceDir/$file > "$exportDir\$file"
            }
        }
    }

    # Verify run_id mapping
    $mappingVerified = $true
    $exportedCount = 0
    Get-ChildItem -Path $exportDir -Filter "*.json" | ForEach-Object {
        $exportedCount++
        $json = Get-Content $_ -Encoding UTF8 | ConvertFrom-Json
        if ($json.run_id -ne $runId) {
            Add-CriticalFailure "Stale capture detected! run_id mismatch in file: $_"
            $mappingVerified = $false
        }
        if ($expectedCaseIds -notcontains $json.case_id) {
            Add-CriticalFailure "Unknown case_id found in capture: $_"
            $mappingVerified = $false
        }
    }
    $report.captures_exported = $exportedCount
    $report.exact_mapping_verified = $mappingVerified

    if ($exportedCount -lt $report.captures_expected) {
        Add-CriticalFailure "Missing captures! Expected , found $exportedCount."
    }

    Write-Host "dY"? Running Replay Tests..."
    Set-Location backend
    pytest tests/test_mobile_scraper_e2e.py -m scraper_replay -v
    if ($LASTEXITCODE -eq 0) {
        $report.replay_passed = $true
    } else {
        Add-CriticalFailure "Replay tests failed"
    }
    Set-Location ..

    if (-not $script:certificationFailed) {
        $report.status = "PASS"
    }

} catch {
    Add-CriticalFailure "Unhandled exception: $_"
} finally {
    if ($script:certificationFailed) {
        if ($report.status -ne "BLOCKED") {
            $report.status = "FAIL"
        }
    }

    if ($backendProcess) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($ADB -and $emulatorProcess) {
        & $ADB emu kill
    }

    $reportJson = $report | ConvertTo-Json -Depth 5
    New-Item -ItemType Directory -Path "artifacts" -Force | Out-Null
    Set-Content -Path "artifacts/scraper_certification_report.json" -Value $reportJson -Encoding UTF8
    Write-Host "dY4 Report written to artifacts/scraper_certification_report.json"

    if ($script:certificationFailed) {
        exit 1
    }
}
