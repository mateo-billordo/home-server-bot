import os
import json
import logging
from dotenv import load_dotenv
from telebot import TeleBot

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0").strip().strip("'\""))
WOL_INTERFACE = os.getenv("WOL_INTERFACE", "wlp3s0")
WOL_TARGETS_FILE = "/app/data/wol_targets.json"

MONITOR_INTERVAL = 300  # seconds (5 min)
DISK_THRESHOLD = 90
MEMORY_THRESHOLD = 90
TEMP_THRESHOLD = 80

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

tgbot = TeleBot(TOKEN, num_threads=2)

with open("messages.json", "r", encoding="utf-8") as f:
    MSGS = json.load(f)


def load_wol_targets() -> dict[str, str]:
    if os.path.exists(WOL_TARGETS_FILE):
        with open(WOL_TARGETS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_wol_targets(targets: dict[str, str]):
    with open(WOL_TARGETS_FILE, "w") as f:
        json.dump(targets, f, indent=2)
