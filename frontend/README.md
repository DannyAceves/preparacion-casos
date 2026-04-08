# Case Prep Staff Frontend

Frontend interno base para staff, construido con Next.js App Router y TypeScript.

## Rutas incluidas

- `/login`
- `/dashboard`
- `/cases`
- `/cases/[caseId]`

## Variables de entorno

1. Copia `.env.example` a `.env.local`.
2. Ajusta la URL del backend y el modo de autenticación.

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=Case Prep Staff
NEXT_PUBLIC_AUTH_MODE=mock
NEXT_PUBLIC_KEYCLOAK_ISSUER=
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=
NEXT_PUBLIC_DEFAULT_ROLE=paralegal
NEXT_PUBLIC_DEFAULT_USER_NAME=Internal Staff
NEXT_PUBLIC_DEFAULT_USER_EMAIL=staff@example.com
```

## Desarrollo

```bash
npm install
npm run dev
```

La aplicación queda disponible en `http://localhost:3000`.

## Notas

- Las rutas internas del staff están protegidas por sesión.
- `mock` crea una sesión placeholder mediante cookie para desarrollo local.
- `keycloak` deja preparado el adapter/config para la futura integración real.
- Los permisos base por rol viven en `src/lib/auth/permissions.ts`.
- El cliente API centralizado está en `src/lib/api/client.ts`.
- El frontend consume el backend existente en tiempo real, sin datos hardcodeados para casos y readiness.
