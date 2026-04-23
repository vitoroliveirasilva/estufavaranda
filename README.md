# Estufa da varanda

Backend Flask para catálogo, acompanhamento e assistência contextual de plantas, com autenticação própria, PostgreSQL, workers agendados, uploads locais seguros e arquitetura em camadas.

## O que está incluído

- Flask com app factory
- Blueprints por módulo
- SQLAlchemy + Flask-Migrate
- PostgreSQL como banco principal
- Autenticação própria com:
  - login por e-mail e senha
  - access token JWT curto
  - refresh token opaco revogável
  - reset de senha por token temporário
  - bloqueio por excesso de tentativas
  - Argon2id para hash de senha
- CRUD de plantas
- Perfis de espécie
- Timeline de eventos
- Upload seguro de fotos
- Registro de rega e score de necessidade de rega
- Clima com provider configurável
- Alertas persistidos e deduplicação
- Assistente contextual por regras com opção de provider externo
- Worker separado para clima, alertas, notificações e limpeza
- Docker Compose com Nginx + API + Worker + PostgreSQL
- Testes com pytest

## Estrutura

```text
estufavaranda/
  .env.example
  docker-compose.yml
  docker/
    api/
      Dockerfile
      entrypoint.sh
    nginx/
      default.conf
  backend/
    app/
      api/
      core/
      models/
      providers/
      repositories/
      schemas/
      services/
      utils/
      workers/
    migrations/
    tests/
    manage.py
    wsgi.py
    requirements.txt
  README.md
```

## Decisões arquiteturais

### 1. Flask em vez de FastAPI
A solução foi adaptada para Flask sem perder as responsabilidades centrais: app factory, separação em camadas, blueprints, validação, workers, notificações, clima, IA e deploy com Docker.

### 2. Access token curto + refresh token opaco
- Access token: JWT assinado e curto
- Refresh token: token aleatório opaco, salvo apenas como hash HMAC no banco
- Vantagem: revogação simples sem confiar cegamente em JWT longo

### 3. Sem cadastro público
Somente administradores criam usuários, o fluxo administrativo está exposto em `/api/v1/admin/users`.

### 4. Upload local seguro no MVP
As fotos ficam em volume local, o banco salva metadados e caminho relativo. O download ocorre por rota protegida.

### 5. IA prudente
O modo padrão é `rules`, com resposta assistida por contexto. É possível ativar um provider externo sem quebrar o fluxo.

## Variáveis de ambiente

Copie `.env.example` para `.env` e ajuste os valores.

Campos essenciais:

- `APP_SECRET_KEY`
- `ACCESS_TOKEN_SECRET`
- `REFRESH_TOKEN_SECRET`
- `DATABASE_URL`
- `UPLOAD_BASE_PATH`

## Subir com Docker

```bash
cp .env.example .env
docker compose up --build -d
```

API:
- `http://localhost/api/v1/health`

## Rodar localmente sem Docker

### 1. Ambiente virtual

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. Banco

Configure um PostgreSQL e ajuste `DATABASE_URL`.

Exemplo:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/estufa_da_varanda
```

### 3. Migrar

```bash
flask --app manage.py db upgrade
```

### 4. Criar admin inicial

```bash
flask --app manage.py create-admin
```

### 5. Rodar API

```bash
flask --app manage.py run --host 0.0.0.0 --port 8000
```

## Worker

O worker roda separado:

```bash
cd backend
python -m app.workers.scheduler
```

Jobs configurados:
- clima: a cada 3 horas
- alertas: a cada 2 horas
- notificações: a cada 5 minutos
- limpeza: 1 vez por dia

## Testes

```bash
cd backend
pytest
```

## Endpoints principais

### Autenticação
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- `POST /api/v1/auth/devices/register`

### Administração
- `GET /api/v1/admin/users`
- `POST /api/v1/admin/users`
- `PATCH /api/v1/admin/users/{id}`
- `PATCH /api/v1/admin/users/{id}/activate`
- `PATCH /api/v1/admin/users/{id}/deactivate`
- `POST /api/v1/admin/users/{id}/reset-password`
- `POST /api/v1/admin/users/{id}/revoke-sessions`
- `GET /api/v1/admin/login-attempts`

### Plantas
- `GET /api/v1/plants`
- `POST /api/v1/plants`
- `GET /api/v1/plants/{id}`
- `PATCH /api/v1/plants/{id}`
- `DELETE /api/v1/plants/{id}`

### Eventos
- `GET /api/v1/plants/{id}/events`
- `POST /api/v1/plants/{id}/events`

### Fotos
- `GET /api/v1/plants/{id}/photos`
- `POST /api/v1/plants/{id}/photos`
- `DELETE /api/v1/plants/{id}/photos/{photo_id}`
- `GET /api/v1/plants/{id}/photos/{photo_id}/download`

### Rega
- `GET /api/v1/plants/{id}/watering-logs`
- `POST /api/v1/plants/{id}/watering-logs`
- `GET /api/v1/plants/{id}/watering-summary`

### Clima
- `GET /api/v1/plants/{id}/climate`
- `GET /api/v1/climate/summary`

### Notificações
- `GET /api/v1/notifications`
- `PATCH /api/v1/notifications/{id}/read`
- `PATCH /api/v1/notifications/{id}/discard`

### IA
- `POST /api/v1/plants/{id}/ai/ask`
- `GET /api/v1/plants/{id}/ai/conversations`

## Observações importantes

- O backend foi desenhado para um MVP em VPS única.
- O provider de clima padrão usa Open-Meteo.
- O provider de IA externo é opcional.
- O acesso administrativo global às plantas pode ser controlado por `ENABLE_ADMIN_READ_ALL_PLANTS`.
- O fluxo de reset de senha envia e-mail quando SMTP estiver configurado. Sem SMTP, o link é logado para ambiente controlado.
- A exclusão de planta é arquivamento lógico.
- A exclusão de foto é remoção lógica controlada.
- O projeto prioriza previsibilidade, clareza e evolução segura, sem microservicite ornamental.
