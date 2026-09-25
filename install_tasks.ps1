param([Parameter(Mandatory=$true)][string]$Executable)
$ErrorActionPreference = "Stop"
$taskNames = @("Radar de Lotes 08h", "Radar de Lotes 14h", "Radar de Lotes 20h")
$times = @("08:00", "14:00", "20:00")
$action = New-ScheduledTaskAction -Execute $Executable -Argument "--scheduled"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
for ($i = 0; $i -lt $taskNames.Count; $i++) {
    $trigger = New-ScheduledTaskTrigger -Daily -At $times[$i]
    Register-ScheduledTask -TaskName $taskNames[$i] -Action $action -Trigger $trigger -Settings $settings -Description "Busca automática do Radar de Lotes" -Force | Out-Null
}
