function slh {
    param([string]$cmd, [string]$target)

    switch ($cmd) {
        "status" {
            Write-Output "SLH STATUS: OK (placeholder)"
        }

        "scan" {
            Write-Output "Scanning: $target"
        }

        "restart" {
            Write-Output "Restarting: $target"
        }

        "deploy" {
            Write-Output "Deploying: $target"
        }

        default {
            Write-Output "Unknown command"
        }
    }
}