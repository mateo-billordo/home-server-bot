import subprocess
import psutil
import shutil

from bot.config import MSGS, SSH_KEY_PATH


def get_system_status() -> str:
    uptime = subprocess.run(["uptime", "-p"], capture_output=True, text=True).stdout.strip()
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    mem = psutil.virtual_memory()
    mem_used = mem.used / (1024**3)
    mem_total = mem.total / (1024**3)
    disk = shutil.disk_usage("/")
    disk_used = disk.used / (1024**3)
    disk_total = disk.total / (1024**3)
    disk_percent = (disk.used / disk.total) * 100
    load = psutil.getloadavg()

    temps = psutil.sensors_temperatures()
    temp_str = "N/A"
    if temps:
        for _, entries in temps.items():
            if entries:
                temp_str = f"{entries[0].current:.0f}°C"
                break

    lines = [
        MSGS["status_title"],
        "",
        MSGS["status_uptime"].format(uptime=uptime),
        MSGS["status_cpu"].format(percent=cpu_percent, cores=cpu_count),
        MSGS["status_load"].format(l1=load[0], l5=load[1], l15=load[2]),
        MSGS["status_ram"].format(used=mem_used, total=mem_total, percent=mem.percent),
        MSGS["status_disk"].format(used=disk_used, total=disk_total, percent=disk_percent),
        MSGS["status_temp"].format(temp=temp_str),
    ]
    return "\n".join(lines)


def get_docker_status() -> str:
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return MSGS["docker_error"]

    lines = [MSGS["docker_title"], ""]
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            name, status = parts
            emoji = "🟢" if "Up" in status else "🔴"
            lines.append(f"{emoji} `{name}` — {status}")
    if len(lines) == 2:
        lines.append(MSGS["docker_empty"])
    return "\n".join(lines)


def get_network_status() -> str:
    result = subprocess.run(["ip", "-br", "addr"], capture_output=True, text=True)
    lines = [MSGS["network_title"], ""]
    for line in result.stdout.strip().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            iface = parts[0]
            state = parts[1]
            addrs = " ".join(parts[2:]) if len(parts) > 2 else ""
            if iface.startswith(("veth", "br-", "docker")) or iface == "lo":
                continue
            emoji = "🟢" if state in ("UP", "UNKNOWN") else "🔴"
            lines.append(f"{emoji} `{iface}` ({state}) {addrs}")
    return "\n".join(lines)


def get_wireguard_status() -> str:
    result = subprocess.run(["wg", "show"], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        return MSGS["vpn_inactive"]

    lines = [MSGS["vpn_title"], ""]
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line.startswith("interface:"):
            lines.append(f"  Interface: `{line.split(':')[1].strip()}`")
        elif line.startswith("listening port:"):
            lines.append(f"  Puerto: `{line.split(':')[1].strip()}`")
        elif line.startswith("peer:"):
            lines.append(f"  Peer: `{line.split(':')[1].strip()[:12]}...`")
        elif "latest handshake" in line:
            lines.append(f"  Último handshake: `{line.split(':', 1)[1].strip()}`")
        elif "transfer" in line:
            lines.append(f"  Tráfico: `{line.split(':', 1)[1].strip()}`")
    return "\n".join(lines)


def restart_wireguard() -> tuple[bool, str]:
    down = subprocess.run(["wg-quick", "down", "wg0"], capture_output=True, text=True)
    up = subprocess.run(["wg-quick", "up", "wg0"], capture_output=True, text=True)
    if up.returncode == 0:
        return (True, MSGS["vpn_restarted"])
    error = up.stderr.strip() or down.stderr.strip() or "Error desconocido"
    return (False, MSGS["vpn_restart_error"].format(error=error))


def normalize_mac(mac: str) -> str:
    mac = mac.strip().upper().replace("-", ":").replace(".", ":")
    if len(mac) == 12 and ":" not in mac:
        mac = ":".join(mac[i:i+2] for i in range(0, 12, 2))
    return mac


def send_wol(mac: str, interface: str) -> tuple[bool, str]:
    mac = normalize_mac(mac)
    result = subprocess.run(
        ["etherwake", "-i", interface, mac],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return (True, mac)
    return (False, result.stderr.strip() or "Error desconocido")


def shutdown_device(host: str, user: str) -> tuple[bool, str]:
    """Shutdown a remote device via SSH. Returns (success, error_message)."""
    result = subprocess.run(
        ["ssh", "-i", SSH_KEY_PATH,
         "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=5",
         f"{user}@{host}", "shutdown /s /t 0"],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode == 0:
        return (True, "")
    return (False, result.stderr.strip() or result.stdout.strip() or "Error desconocido")
