# 🎬 Overseerr Telegram Bot

Bot de Telegram para solicitar películas y series en [Overseerr](https://overseerr.dev) sin necesidad de abrir la plataforma.

## Comandos

| Comando | Descripción |
|---|---|
| `/start` | Muestra el estado de tu cuenta y los comandos disponibles |
| `/vincular <email>` | Vincula tu cuenta de Overseerr por email |
| `/desvincular` | Desvincula tu cuenta de Overseerr |
| `/buscar <nombre>` | Busca una película o serie y solicítala con un solo click |
| `/peticiones` | Ver tus peticiones y su estado |

## Autorización

Solo los usuarios vinculados a una cuenta de Overseerr pueden usar el bot.

```
/vincular juan@ejemplo.com  →  ✅ Vinculado como "Juan"
/buscar Interstellar         →  🎬 Resultados con botón de solicitud
[click en resultado]         →  ✅ Solicitada en tu nombre
/peticiones                  →  📋 Tus peticiones y su estado
```

Si el email no existe en Overseerr, el bot rechaza la vinculación y el usuario no puede hacer búsquedas ni peticiones.

## Notificaciones automáticas

El bot comprueba periódicamente el estado de las peticiones y notifica al usuario cuando cambia:

| Cambio | Notificación |
|---|---|
| Aprobada | ✅ Tu petición de *Interstellar* ha sido aprobada. |
| Disponible | 🟢 *Interstellar* ya está disponible. |
| Rechazada | ❌ Tu petición de *Interstellar* ha sido rechazada. |
| Procesando | 🔄 *Interstellar* está siendo procesada. |

El intervalo de consulta se configura con `POLL_INTERVAL_HOURS` (por defecto 12 horas).

## Requisitos

- Docker y Docker Compose
- Un bot de Telegram (creado con [@BotFather](https://t.me/BotFather))
- Una instancia de Overseerr en funcionamiento
- API Key de Overseerr

## Instalación

### 1. Clona el repositorio

```bash
git clone https://github.com/Ratz77/overseerr-bot.git
cd overseerr-bot
```

### 2. Configura el entorno

```bash
cp .env.example .env
```

Edita `.env` con tus datos:

```env
# Token del bot de Telegram (obtenido de @BotFather)
TELEGRAM_TOKEN=tu_token_aqui

# URL de tu instancia de Overseerr
OVERSEERR_URL=http://192.168.1.10:5055

# API Key de Overseerr (Settings → General → API Key)
OVERSEERR_API_KEY=tu_api_key_aqui

# Opcional: IDs de Telegram separados por coma que pueden usar el bot
# Si se deja vacío, cualquier usuario puede intentar vincularse
ALLOWED_USERS=123456789,987654321

# Intervalo en horas para comprobar cambios en las peticiones (por defecto 12)
POLL_INTERVAL_HOURS=12
```

### 3. Arranca con Docker

```bash
docker compose up -d
```

### 4. Ver logs

```bash
docker compose logs -f
```

## Obtener tu ID de Telegram

Para restringir el bot a usuarios concretos mediante `ALLOWED_USERS`, necesitas el ID numérico de Telegram de cada usuario. Se puede obtener hablando con [@userinfobot](https://t.me/userinfobot).

## Estados de las peticiones

| Estado | Significado |
|---|---|
| ⏳ Pendiente | Esperando aprobación |
| ✅ Aprobada | Aprobada, en descarga |
| 🔄 Procesando | Siendo procesada |
| 🟢 Disponible | Ya disponible para ver |
| ❌ Rechazada | Rechazada por el administrador |

## Estructura del proyecto

```
overseerr-bot/
├── bot.py           # Lógica del bot y comandos
├── overseerr.py     # Cliente de la API de Overseerr
├── notifier.py      # Notificador de cambios de estado (poller)
├── storage.py       # Gestión de usuarios y estados (users.json, states.json)
├── config.py        # Carga de variables de entorno
├── .env.example     # Plantilla de configuración
├── Dockerfile
└── docker-compose.yml
```

## Tecnologías

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v20
- [httpx](https://www.python-httpx.org/) para llamadas async a la API
- [Overseerr API](https://api-docs.overseerr.dev/)
