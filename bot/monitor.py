import subprocess
import psutil
import shutil

from bot.config import MSGS


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
            if iface.startswith(("veth", "br-", "docker")):
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


def send_wol(mac: str, interface: str) -> tuple[bool, str]:
    result = subprocess.run(
        ["etherwake", "-i", interface, mac],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return (True, MSGS["wol_success"].format(mac=mac))
    return (False, MSGS["wol_error"].format(error=result.stderr.strip() or "Error desconocido"))
