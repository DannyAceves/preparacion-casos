param(
    [switch]$Seed
)

docker compose up --build -d postgres redis api worker frontend

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if ($Seed) {
    docker compose --profile tools run --rm seed
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

docker compose ps
