import time
import shutil
import psutil

from bot.config import tgbot, ADMIN_ID, MSGS, log, MONITOR_INTERVAL, DISK_THRESHOLD, MEMORY_THRESHOLD, TEMP_THRESHOLD


def health_watcher():
    """Background thread: periodic health checks, alerts on thresholds."""
    log.info("Health watcher started (every %ds)", MONITOR_INTERVAL)
    time.sleep(30)

    while True:
        try:
            alerts = []

            disk = shutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent >= DISK_THRESHOLD:
                alerts.append(MSGS["health_disk"].format(percent=disk_percent))

            mem = psutil.virtual_memory()
            if mem.percent >= MEMORY_THRESHOLD:
                alerts.append(MSGS["health_memory"].format(percent=mem.percent))

            temps = psutil.sensors_temperatures()
            if temps:
                for _, entries in temps.items():
                    if entries and entries[0].current >= TEMP_THRESHOLD:
                        alerts.append(MSGS["health_temp"].format(temp=entries[0].current))
                        break

            if alerts:
                msg = MSGS["health_alert"] + "\n".join(alerts)
                tgbot.send_message(ADMIN_ID, msg, parse_mode="Markdown")

        except Exception as e:
            log.error("Health watcher error: %s", e)

        time.sleep(MONITOR_INTERVAL)
