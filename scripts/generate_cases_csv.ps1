$casesJson = Get-Content "certification/cases.json" | ConvertFrom-Json
$csvPath = "mobile/.maestro/scraper-certification/cases.csv"
$casesJson | Select-Object case_id, domain, provider, query, location_profile | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
