# Home Server Bot

Telegram bot for monitoring the home server, waking and shutting down remote devices.

## Features

- **System monitoring** — CPU, RAM, disk, temperature, load average
- **Docker status** — list running containers and their health
- **Network info** — interfaces, IPs, connection state
- **WireGuard VPN** — connection status, peers, traffic, restart
- **Power management** — Wake-on-LAN + remote shutdown (SSH) from a unified menu
- **Proactive alerts** — notifies admin when disk/RAM/temp cross thresholds

## Menu

```
🖥️ Estado    | 🐳 Docker
🌐 Red       | 🔒 VPN
⚡ Power

Power sub-panel:
  ├── ⚡ PC-Mateo  (send WOL)
  ├── 🔴 PC-Mateo  (shutdown via SSH — with confirmation)
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
bash deploy.sh
```

Use `--force` if you changed volumes or network config:

```bash
bash deploy.sh --force
```

### 4. Add devices

Use the bot's ⚡ Power → ➕ Agregar dispositivo menu. The flow asks for:

1. **Name** — display name (e.g., `PC-Mateo`)
2. **MAC** — for Wake-on-LAN (e.g., `AA:BB:CC:DD:EE:FF`)
3. **Host** — IP/hostname for SSH shutdown (type `-` to skip)
4. **User** — SSH username on the remote machine

Data is stored in `data/wol_targets.json`:

```json
{
  "PC-Mateo": {
    "mac": "AA:BB:CC:DD:EE:FF",
    "host": "192.168.0.50",
    "user": "mateo"
  }
}
```

### 5. SSH shutdown setup (Windows target)

The bot shuts down remote machines via `ssh user@host "shutdown /s /t 0"`.

**On the Windows PC:**

1. Enable OpenSSH Server:
   - Settings → Apps → Optional Features → Add a feature → OpenSSH Server → Install
   - Services → "OpenSSH SSH Server" → Start + set to Automatic

2. Add the homeserver's public key:
   ```powershell
   # Get key from homeserver:
   # cat ~/.ssh/id_rsa.pub
   #
   # Paste into one of:
   #   C:\Users\<you>\.ssh\authorized_keys          (standard user)
   #   C:\ProgramData\ssh\administrators_authorized_keys  (admin user)
   ```

3. Test from homeserver:
   ```bash
   ssh -i ~/.ssh/id_rsa mateo@192.168.0.50 "echo works"
   ```

**On the homeserver:** the `docker-compose.yml` mounts `~/.ssh/id_rsa` (read-only) into the container.

## Requirements

- Docker + Docker Compose
- `network_mode: host` (required for WOL broadcast and system monitoring)
- `cap_add: NET_ADMIN` (required for WireGuard status and restart)
- Docker socket mounted (for container status)
- SSH private key mounted (for remote shutdown)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_TOKEN` | — | Bot token from @BotFather |
| `ADMIN_ID` | — | Your Telegram chat ID |
| `WOL_INTERFACE` | `wlp3s0` | Network interface for WOL packets |
| `SSH_KEY_PATH` | `/app/ssh/id_rsa` | Path to SSH private key inside container |

## Project Structure

```
home-server-bot/
├── bot/
│   ├── __init__.py
│   ├── config.py        # Configuration, bot instance, device targets
│   ├── monitor.py       # System monitoring, WOL, SSH shutdown
│   ├── keyboards.py     # Inline keyboard builders
│   ├── handlers.py      # Telegram command + callback handlers
│   ├── watcher.py       # Background health alert thread
│   └── main.py          # Entry point
├── data/
│   └── wol_targets.json # Device registry (persistent volume)
├── messages.json        # UI strings (Spanish)
├── Dockerfile
├── docker-compose.yml
├── deploy.sh
├── .env.example
└── .gitignore
```
