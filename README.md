# 🎬 Overseerr Telegram Bot

Bot de Telegram para solicitar películas y series en [Overseerr](https://overseerr.dev) sin necesidad de abrir la plataforma. Funciona tanto en chats privados como en grupos.

---

## Comandos

| Comando | Descripción |
|---|---|
| `/start` | Muestra el estado de tu cuenta y los comandos disponibles |
| `/vincular` | Vincula tu cuenta de Overseerr por email (privado y seguro) |
| `/desvincular` | Desvincula tu cuenta de Overseerr |
| `/buscar <nombre>` | Busca una película o serie y solicítala con un click |
| `/peticiones` | Ver tus peticiones y su estado actual |
| `/cancelar` | Cancela el proceso de vinculación en curso |

---

## Vinculación de cuenta

Solo los usuarios vinculados a una cuenta de Overseerr pueden hacer peticiones. El email nunca es visible en el grupo.

### En chat privado

```
/vincular
Bot: 🔒 Introduce tu email de Overseerr:
Tú: juan@ejemplo.com
Bot: ✅ Cuenta vinculada como "Juan"
```

### En un grupo

```
Tú:  /vincular
Bot: @juan, pulsa el botón para vincular tu cuenta.
     [ 🔒 Vincular en privado ]  ← abre el chat privado automáticamente

[chat privado]
Bot: 🔒 Introduce tu email de Overseerr:
Tú: juan@ejemplo.com
Bot: ✅ Cuenta vinculada. Ya puedes hacer peticiones.

[grupo]
Bot: ✅ @juan ya está vinculado y puede hacer peticiones.
```

La vinculación se guarda permanentemente. No es necesario repetirla en futuras sesiones.

Si el email no existe en Overseerr, el bot rechaza la vinculación y el usuario no puede buscar ni solicitar contenido.

---

## Búsqueda y peticiones

```
/buscar Interstellar

Bot: Resultados para Interstellar:
     🎬 Interstellar (2014)
     🎬 Interstellar (2014) · Disponible en Plex
     📺 Interstellar: Nolan's Odyssey · Ya está solicitada
```

Al pulsar un resultado, el bot realiza la petición en Overseerr en nombre del usuario:

```
✅ Interstellar solicitada por @juan.
Estado: ⏳ Pendiente
```

### Estados en los botones de búsqueda

| Etiqueta en el botón | Significado |
|---|---|
| _(sin etiqueta)_ | Disponible para solicitar |
| `Ya está solicitada` | Pendiente de aprobación |
| `Procesando` | Descargando |
| `Parcialmente disponible` | Algunas temporadas disponibles |
| `Disponible en Plex` | Ya en Plex |

---

## Advertencias de contenido

El bot detecta automáticamente series turcas, latinas y telenovelas e incluye un aviso al realizar la petición:

```
✅ Kara Sevda solicitada por @juan.
Estado: ⏳ Pendiente

⚠️ Esta es una serie turca, es muy probable que la petición sea rechazada.
```

Cada tipo de advertencia se puede activar o desactivar individualmente desde `.env`.

---

## Notificaciones automáticas

El bot comprueba periódicamente el estado de las peticiones y notifica al usuario cuando cambia:

| Cambio de estado | Notificación |
|---|---|
| Aprobada | ✅ Tu petición de *Interstellar* ha sido aprobada. |
| Disponible | 🟢 *Interstellar* ya está disponible. |
| Rechazada | ❌ Tu petición de *Interstellar* ha sido rechazada. |
| Procesando | 🔄 *Interstellar* está siendo procesada. |

El intervalo se configura con `POLL_INTERVAL_HOURS` (por defecto 12 horas). En la primera ejecución guarda el estado actual sin notificar, para evitar spam con peticiones antiguas.

---

## Requisitos

- Docker y Docker Compose
- Un bot de Telegram — creado con [@BotFather](https://t.me/BotFather)
- Una instancia de Overseerr en funcionamiento
- API Key de Overseerr

---

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

# Advertencias al solicitar contenido de origen específico (true/false)
WARN_TURKISH=true
WARN_LATIN=true
WARN_TELENOVELA=true
```

### 3. Arranca con Docker

```bash
docker compose up -d
```

### 4. Ver logs

```bash
docker compose logs -f
```

---

## Obtener tu ID de Telegram

Para usar `ALLOWED_USERS`, necesitas el ID numérico de cada usuario. Puedes obtenerlo hablando con [@userinfobot](https://t.me/userinfobot).

---

## Estructura del proyecto

```
overseerr-bot/
├── bot.py            # Lógica del bot y comandos
├── overseerr.py      # Cliente de la API de Overseerr
├── notifier.py       # Notificador de cambios de estado (poller)
├── storage.py        # Gestión de usuarios y estados (users.json, states.json)
├── config.py         # Carga de variables de entorno
├── .env.example      # Plantilla de configuración
├── Dockerfile
└── docker-compose.yml
```

Los datos de usuarios y estados se guardan en `./data/` y persisten entre reinicios del contenedor.

---

## Tecnologías

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v20
- [httpx](https://www.python-httpx.org/) para llamadas async a la API
- [Overseerr API](https://api-docs.overseerr.dev/)
