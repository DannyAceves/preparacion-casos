# Case Prep Platform

Plataforma de preparacion de casos legales y migratorios con backend en FastAPI, frontend interno en Next.js y procesamiento documental asincrono con Redis workers.

## Servicios

El proyecto queda preparado para levantar con Docker Compose:

- `frontend`: interfaz interna del staff
- `api`: backend FastAPI
- `worker`: procesamiento documental asincrono
- `postgres`: base de datos
- `redis`: broker y cola
- `migrate`: utilidad de migraciones
- `seed`: utilidad de datos demo
- `test-e2e`: utilidad para la suite end-to-end base

## Archivos de despliegue

- [docker-compose.yml](/d:/PROGRAMACION/Portafolio/PREPARACION_CASOS/docker-compose.yml): base reusable para staging
- [docker-compose.override.yml](/d:/PROGRAMACION/Portafolio/PREPARACION_CASOS/docker-compose.override.yml): ajustes locales de desarrollo
- [.env.example](/d:/PROGRAMACION/Portafolio/PREPARACION_CASOS/.env.example): ejemplo para local
- [.env.staging.example](/d:/PROGRAMACION/Portafolio/PREPARACION_CASOS/.env.staging.example): ejemplo para staging
- [Dockerfile](/d:/PROGRAMACION/Portafolio/PREPARACION_CASOS/Dockerfile): imagen backend y worker
- [frontend/Dockerfile](/d:/PROGRAMACION/Portafolio/PREPARACION_CASOS/frontend/Dockerfile): imagen frontend con targets `dev` y `runner`

## Requisitos

- Docker Desktop o Docker Engine con Compose

## Local

1. Copia `.env.example` a `.env`.
2. Crea la carpeta `storage` si quieres inspeccionar archivos locales fuera del contenedor.
3. Levanta la plataforma:

```bash
docker compose up --build
```

Como existe [docker-compose.override.yml](/d:/PROGRAMACION/Portafolio/PREPARACION_CASOS/docker-compose.override.yml), en local se activan automaticamente:

- bind mounts del codigo
- `uvicorn --reload`
- frontend en modo `next dev`
- storage documental en `./storage`

URLs locales:

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

PowerShell:

```powershell
./scripts/bootstrap_local.ps1
```

Shell:

```bash
sh ./scripts/bootstrap_local.sh
```

## Staging Simple

1. Copia `.env.staging.example` a `.env.staging`.
2. Ajusta credenciales y puertos.
3. Levanta solo el compose base:

```bash
docker compose -f docker-compose.yml --env-file .env.staging up --build -d
```

Eso evita aplicar el override local y deja:

- API sin `--reload`
- frontend en build `runner` con `next start`
- volumen interno para storage documental
- cookies mock marcadas como `secure`
- docs OpenAPI deshabilitadas fuera de desarrollo

PowerShell:

```powershell
./scripts/bootstrap_staging.ps1
```

Shell:

```bash
sh ./scripts/bootstrap_staging.sh
```

## Migraciones, Seed y E2E

Local con override:

```bash
docker compose --profile tools run --rm migrate
docker compose --profile tools run --rm seed
docker compose --profile tools run --rm test-e2e
```

Local con scripts:

```powershell
./scripts/migrate_local.ps1
./scripts/seed_local.ps1
./scripts/test_e2e_local.ps1
```

```bash
sh ./scripts/migrate_local.sh
sh ./scripts/seed_local.sh
sh ./scripts/test_e2e_local.sh
```

Staging simple:

```bash
docker compose -f docker-compose.yml --env-file .env.staging --profile tools run --rm migrate
docker compose -f docker-compose.yml --env-file .env.staging --profile tools run --rm seed
```

## Hardening Basico

Se agrego una base minima para staging y beta interna:

- logging estructurado en API y worker
- middleware con `x-request-id` y `x-response-time-ms`
- manejo consistente de errores en backend con payload uniforme
- validacion estricta de entorno en backend y frontend
- cookies mock `httpOnly` y `secure` en entornos tipo staging/production
- docs OpenAPI expuestas solo en desarrollo
- limite de uploads validado desde `DOCUMENT_MAX_SIZE_BYTES`
- health checks de API, frontend, postgres, redis y worker en Compose

Health endpoints del backend:

- `GET /health`
- `GET /health/live`
- `GET /health/ready`

Health endpoint del frontend:

- `GET /api/health`

## Backups Simples

Base de datos:

```powershell
./scripts/backup_db_local.ps1
```

```bash
sh ./scripts/backup_db_local.sh
```

Storage documental:

```powershell
./scripts/backup_storage_local.ps1
```

```bash
sh ./scripts/backup_storage_local.sh
```

Los backups se guardan en la carpeta local `backups/`.

## Dataset demo

El seed crea un dataset reproducible para QA con:

- usuarios internos mock para `admin`, `attorney`, `paralegal` y `qa`
- `case_type`: `family-based`, `employment-based`, `humanitarian`
- 6 casos `CASE-QA-*` con estados variados
- templates de cuestionario y respuestas
- documentos de ejemplo y versionado
- campos canonicos, inconsistencias, reviews, packet, forms y submissions

Referencias generadas:

- `storage/seed-reference/staff-users.json`
- `storage/seed-reference/case-types.json`
- `storage/seed-reference/cases.json`

Usuarios mock recomendados para login local:

- `admin.qa@example.com`
- `attorney.qa@example.com`
- `paralegal.qa@example.com`
- `qa.reviewer@example.com`

## Suite E2E

La base E2E vive en [tests/e2e/conftest.py](/d:/PROGRAMACION/Portafolio/PREPARACION_CASOS/tests/e2e/conftest.py) y [tests/e2e/test_case_lifecycle_e2e.py](/d:/PROGRAMACION/Portafolio/PREPARACION_CASOS/tests/e2e/test_case_lifecycle_e2e.py).

Cubre:

- crear cliente
- crear caso
- responder cuestionario
- subir documento
- reprocesar documento
- revisar y actualizar canonical fields
- resolver inconsistencia
- generar y aprobar formulario
- generar packet
- aprobar submission
- marcar submitted
- cerrar caso
- escenario bloqueado por readiness

Cuando falla una prueba, las aserciones incluyen `response.text` para dejar evidencia clara del error devuelto por la API.

## Desarrollo sin Docker

Backend:

```bash
pip install -e .[dev]
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Pruebas:

```bash
pytest
pytest tests/e2e -q
```

## Notas de autenticacion

- El frontend ya incluye una base preparada para integracion futura con Keycloak.
- En local, `NEXT_PUBLIC_AUTH_MODE=mock` usa una sesion placeholder por cookie.
- No hay secretos reales hardcodeados en los archivos de despliegue.

## RBAC Backend

El backend ahora aplica RBAC formal sobre los endpoints internos con cinco roles:

- `admin`: acceso total, gestion de cuentas, asignacion de roles, templates, cuestionarios base, checklist templates, configuracion y audit logs.
- `reception`: intake/consultations, agenda, captura inicial y clasificacion preliminar. No puede operar expediente formal ni aprobaciones.
- `attorney`: puede operar casos asignados, checklist, questionnaire, canonical fields, inconsistencies, forms, readiness, reviews y submission final.
- `paralegal`: puede operar casos asignados, documentos, checklist, procesamiento, extraccion, forms, packet y ejecucion de submission ya aprobada. No puede aprobar submission final ni forms.
- `client`: acceso restringido a su portal y a sus propios recursos cuando aplique.

### Matriz resumida

- `admin/users`: solo `admin`; listado, busqueda, alta, edicion, asignacion de rol y activacion/desactivacion de cuentas
- `consultations`: `admin`, `reception`; conversion a caso tambien `attorney` y `paralegal`
- `clients`: staff interno segun permiso; eliminacion solo `admin`
- `cases`: `admin`, `attorney`, `paralegal`
- `questionnaire-templates`, `questionnaires`, `questionnaire-responses`, `audit-logs`, `participants`: solo `admin`
- `generated forms`:
  - workspace y preparacion: `admin`, `attorney`, `paralegal`
  - aprobacion/fix required: `admin`, `attorney`
- `submission`:
  - aprobar/cerrar: `admin`, `attorney`
  - submit/fail: `admin`, `attorney`, `paralegal`
- `client portal`: el staff emite accesos desde endpoints protegidos; el portal publico sigue autenticando por `token + passcode`

### Ownership y asignacion

- `admin` siempre puede acceder.
- `client` solo puede acceder a recursos del `client_id` asociado a su principal.
- `attorney` y `paralegal` pueden operar casos asignados. Hoy el backend acepta `assigned_case_ids` desde el principal normalizado, dejando el hook listo para claims de Keycloak sin introducir un modelo local de usuarios.
- Consultations con `assigned_attorney` quedan restringidas a ese abogado cuando aplica.

### Principal actual y compatibilidad con Keycloak

Mientras llega la integracion final con Keycloak, el backend acepta un principal ligero por headers:

- `X-Principal-Subject`
- `X-Principal-Roles`
- `X-Principal-Client-Id` opcional
- `X-Principal-Email` opcional
- `X-Principal-Case-Ids` opcional, lista CSV de UUIDs asignados

Cuando exista middleware real de Keycloak, este solo debe poblar `request.state.authenticated_principal` con la misma forma normalizada y el resto del RBAC seguira funcionando sin reescribir las rutas.

## Variables nuevas relevantes

- `LOG_LEVEL`
- `FRONTEND_APP_URL`
- `NEXT_PUBLIC_APP_ENV`

En staging, usa `https` en `FRONTEND_APP_URL` y manten `APP_DEBUG=false`.
