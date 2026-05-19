# 🎬 Overseerr Telegram Bot

Bot de Telegram para solicitar películas y series en [Overseerr](https://overseerr.dev) sin necesidad de abrir la plataforma.

## Comandos

| Comando | Descripción |
|---|---|
| `/start` | Muestra la ayuda y comandos disponibles |
| `/buscar <nombre>` | Busca una película o serie y la solicita con un solo click |
| `/peticiones` | Lista las últimas peticiones y su estado |

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
# Si se deja vacío, cualquier usuario puede usarlo
ALLOWED_USERS=123456789,987654321
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

Para restringir el bot a usuarios concretos, necesitas tu ID numérico de Telegram. Puedes obtenerlo hablando con [@userinfobot](https://t.me/userinfobot).

## Estados de las peticiones

| Estado | Significado |
|---|---|
| ⏳ Pendiente | Esperando aprobación |
| ✅ Aprobada | Aprobada, en descarga |
| 🔄 Procesando | Siendo procesada |
| 🟢 Disponible | Ya disponible para ver |
| ❌ Rechazada | Rechazada por el administrador |

## Tecnologías

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v20
- [httpx](https://www.python-httpx.org/) para llamadas async a la API
- [Overseerr API](https://api-docs.overseerr.dev/)
