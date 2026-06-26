import threading

from bot.config import tgbot, log
import bot.handlers  # noqa: F401 — registers handlers via decorators
from bot.watcher import health_watcher


def main():
    threading.Thread(target=health_watcher, daemon=True).start()
    log.info("Home server bot starting...")
    tgbot.infinity_polling()


if __name__ == '__main__':
    main()
