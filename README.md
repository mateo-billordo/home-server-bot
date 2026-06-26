# Home Server Bot

Telegram bot for monitoring the home server and sending Wake-on-LAN packets remotely.

## Features

- **System monitoring** — CPU, RAM, disk, temperature, load average
- **Docker status** — list running containers and their health
- **Network info** — interfaces, IPs, connection state
- **WireGuard VPN** — connection status, peers, traffic
- **Wake-on-LAN** — wake configured devices from anywhere via Telegram
- **Proactive alerts** — notifies admin when disk/RAM/temp cross thresholds

## Menu

```
🖥️ Estado    | 🐳 Docker
🌐 Red       | 🔒 VPN
⚡ Wake-on-LAN
  ├── ⚡ PC-Mateo (send WOL)
  ├── ➕ Agregar dispositivo
  ├── 🗑️ Eliminar dispositivo
  └── ← Volver
```

## Setup

### 1. Create a Telegram bot

Talk to @BotFather, get a token.

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your token and Telegram chat ID
```

### 3. Deploy

```bash
docker compose build --no-cache
docker compose up -d
```

### 4. Add WOL targets

Use the bot's ⚡ Wake-on-LAN → ➕ Agregar dispositivo menu. Or edit `wol_targets.json` directly:

```json
{
  "PC-Mateo": "AA:BB:CC:DD:EE:FF"
}
```

## Requirements

- Docker + Docker Compose
- `network_mode: host` (required for WOL broadcast and system monitoring)
- Docker socket mounted (for container status)
- `etherwake` available in container
- WireGuard requires `sudo wg` — container runs as root

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_TOKEN` | — | Bot token from @BotFather |
| `ADMIN_ID` | — | Your Telegram chat ID |
| `WOL_INTERFACE` | `wlp3s0` | Network interface for WOL packets |

## Project Structure

```
home-server-bot/
├── bot/
│   ├── __init__.py
│   ├── config.py        # Configuration, bot instance, WOL targets
│   ├── monitor.py       # System monitoring + WOL functions
│   ├── keyboards.py     # Inline keyboard builders
│   ├── handlers.py      # Telegram command + callback handlers
│   ├── watcher.py       # Background health alert thread
│   └── main.py          # Entry point
├── messages.json        # UI strings (Spanish)
├── wol_targets.json     # WOL device registry (persistent volume)
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── .gitignore
```
