$taskNames = @("Radar de Lotes 08h", "Radar de Lotes 14h", "Radar de Lotes 20h")
foreach ($name in $taskNames) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
}
