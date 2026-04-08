$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force -Path backups | Out-Null
$dbUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "caseprep" }
$dbName = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "caseprep" }
docker compose exec -T postgres pg_dump -U $dbUser $dbName | Out-File -Encoding utf8 "backups/db-$stamp.sql"
Write-Output "Database backup created at backups/db-$stamp.sql"
