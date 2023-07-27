Add-Type -AssemblyName PresentationCore, PresentationFramework
Add-Type -AssemblyName System.Windows.Forms

# Define the path to the XAML file
$xamlPath = (Get-Item "ui.xaml").fullname

# Create a XML reader to read the XAML file
$reader = [System.Xml.XmlReader]::Create($xamlPath)
$timer = New-Object System.Windows.Forms.Timer

try {
    # Load the XAML file
    $wpfWindow = [Windows.Markup.XamlReader]::Load($reader)
    $processListView = $wpfWindow.FindName("processListView")

    # Function to update the process list
    function UpdateProcessList {
        Write-Host "updated on" $(get-date)

        $processes = Get-Process | Sort-Object -Property ProcessName -Unique

        $query = "SELECT IDProcess,IOWriteOperationsPersec, IOWriteBytesPersec FROM Win32_PerfFormattedData_PerfProc_Process"
        $win32_processes = Get-WmiObject -Query $query | Group-Object -AsHashTable -Property IDProcess

        $data = New-Object 'System.Collections.Generic.List[PSCustomObject]'

        foreach ($process in $processes.GetEnumerator()) {
            if ($process.Id -eq 0) {
                Continue
            }

            $processId = $process.Id

            $win32_process = $win32_processes[$processId]
            $ioUtilization = $win32_process.IOWriteOperationsPersec + $win32_process.IOWriteBytesPersec 
            $cpuUtilization = $process.CPU

            if ($cpuUtilization -gt $ioUtilization) {
                $processType = "CPU-bound"
            }
            else {
                $processType = "I/O-bound"
            }
            $memUsage = [Math]::Round($process.WorkingSet / 1MB, 2)

            $data.Add([PSCustomObject]@{
                ProcessName   = $process.name
                p_id          = $process.id
                CPUUsage      = [Math]::Round($cpuUtilization, 2)
                MEMUsage      = $memUsage
                IOUtilization = $ioUtilization
                IOBound       = $processType
            })
        }

        $processListView.ItemsSource = $data
    }

    # Timer callback function
    $timerCallback = {
        UpdateProcessList
    }
    UpdateProcessList
    # Create a timer that triggers every 10 seconds
    $timer.Interval = 10000 
    $timer.Add_Tick($timerCallback)
    $timer.Start()

    # Show the WPF window
    $wpfWindow.ShowDialog() | Out-Null
}
finally {
    # Close the XML reader
    $reader.Close()

    # Dispose the timer to release resources
    if ($timer -ne $null) {
        $timer.Dispose()
    }
}
