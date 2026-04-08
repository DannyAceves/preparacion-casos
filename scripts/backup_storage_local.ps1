$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force -Path backups | Out-Null
Compress-Archive -Path storage -DestinationPath "backups/storage-$stamp.zip" -Force
Write-Output "Storage backup created at backups/storage-$stamp.zip"
