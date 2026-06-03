# PROMPT 1 — Scaffold completo del proyecto

Lee CLAUDE.md en su totalidad antes de empezar.

Construye el scaffold completo del proyecto respetando exactamente la estructura de carpetas definida en CLAUDE.md.

## Lo que debe quedar funcionando al final

### Backend
- FastAPI arrancando en puerto 8000
- PostgreSQL conectado con SQLAlchemy async
- Alembic configurado con migración inicial que crea estas tablas:
  - `users` (id UUID, email, hashed_password, created_at, updated_at)
  - `plans` (id UUID, user_id FK, title, description, steps JSONB, status ENUM pending_approval/approved/rejected/executing/done, feedback text, created_at, updated_at)
  - `agent_tasks` (id UUID, plan_id FK, agent_name, tool_name, input JSONB, output JSONB, status ENUM pending/running/completed/failed, created_at, updated_at)
  - `chat_messages` (id UUID, user_id FK, role ENUM user/assistant, content text, plan_id FK nullable, created_at)
- Auth JWT funcionando:
  - POST /auth/register
  - POST /auth/login → devuelve access_token
  - GET /auth/me → devuelve usuario autenticado
- Endpoint de chat:
  - POST /chat/message → recibe {content: string}, devuelve mensaje del orquestador (mock por ahora)
- Endpoint de planes:
  - GET /plans → lista planes del usuario
  - GET /plans/{id} → detalle de un plan
  - POST /plans/{id}/approve → cambia estado a approved
  - POST /plans/{id}/reject → recibe {feedback: string}, cambia estado a rejected
- WebSocket en /ws/{user_id} → emite eventos cuando cambia el estado de un plan o tarea
- Redis conectado (solo configurado, sin uso todavía)
- Celery configurado (solo worker base, sin tareas todavía)

### Frontend
- Vite + React 18 + TypeScript arrancando en puerto 5173
- TailwindCSS configurado
- React Router con estas rutas:
  - / → redirige a /chat
  - /login → página de login
  - /register → página de registro
  - /chat → página principal (protegida)
  - /dashboard → dashboard de supervisión (protegida)
- Zustand store para: usuario autenticado, mensajes del chat, planes pendientes
- Cliente HTTP en src/lib/api.ts con interceptor que añade JWT header
- Hook useWebSocket.ts que conecta al WS del backend
- Layout base con sidebar izquierdo (Chat, Dashboard, nav) y área principal
- Página /chat con:
  - Lista de mensajes (user y assistant)
  - Input de texto para enviar mensajes
  - Cuando el mensaje del assistant incluye un plan: renderiza ApprovalCard
- ApprovalCard component:
  - Muestra título del plan, descripción y lista de pasos
  - Botón "Aprobar" → llama POST /plans/{id}/approve
  - Botón "Rechazar" → muestra input de feedback → llama POST /plans/{id}/reject
  - Estado visual: pending (amarillo), approved (verde), rejected (rojo)

### Docker Compose
- Servicios: postgres, redis, backend, frontend
- Hot reload en backend (uvicorn --reload) y frontend (Vite HMR)
- Variables desde .env

### Mock del Orquestador
Por ahora POST /chat/message debe:
1. Guardar el mensaje del usuario en chat_messages
2. Generar un plan mock con 3-4 pasos realistas basados en el mensaje del usuario (hardcodeado está bien)
3. Guardar el plan en DB con estado pending_approval
4. Devolver un mensaje de assistant que incluya el plan_id
5. Emitir evento por WebSocket: {type: "new_plan", plan_id: "..."}

## Lo que NO implementar todavía
- Lógica real de agentes (CopyAgent, AdsAgent, etc.)
- Integración con Meta, Google, Resend, Vercel
- Ejecución real de planes aprobados (Celery solo configurado)
- Página de Dashboard (solo el componente vacío con "próximamente")

## Al terminar
Verifica que `docker compose up` levanta todo sin errores y que el flujo completo funciona:
1. Registro de usuario
2. Login
3. Enviar mensaje en /chat
4. Ver ApprovalCard con el plan mock
5. Aprobar o rechazar el plan
6. Ver el estado actualizado en la card
