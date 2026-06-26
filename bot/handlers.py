import subprocess

from bot.config import ADMIN_ID, MSGS, WOL_INTERFACE, tgbot, load_wol_targets, save_wol_targets
from bot.keyboards import build_main_menu, build_wol_menu, build_back_button
from bot.monitor import (
    get_system_status, get_docker_status, get_network_status,
    get_wireguard_status, send_wol,
)

# Multi-step flow state
user_state: dict[int, str] = {}


@tgbot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    if message.chat.id != ADMIN_ID:
        tgbot.reply_to(message, MSGS["unauthorized"])
        return
    tgbot.send_message(message.chat.id, MSGS["welcome"],
                       reply_markup=build_main_menu(), parse_mode="Markdown")


@tgbot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def handle_text(message):
    if message.chat.id != ADMIN_ID:
        return
    chat_id = message.chat.id
    state = user_state.pop(chat_id, None)

    if state == "wol_add_name":
        user_state[chat_id] = f"wol_add_mac:{message.text.strip()}"
        tgbot.reply_to(message, MSGS["wol_prompt_mac"])
        return

    if state and state.startswith("wol_add_mac:"):
        name = state.split(":", 1)[1]
        from bot.monitor import normalize_mac
        mac = normalize_mac(message.text.strip())
        targets = load_wol_targets()
        targets[name] = mac
        save_wol_targets(targets)
        tgbot.reply_to(message, MSGS["wol_added"].format(name=name, mac=mac),
                       reply_markup=build_wol_menu(), parse_mode="Markdown")
        return

    if state == "wol_remove":
        name = message.text.strip()
        targets = load_wol_targets()
        if name in targets:
            del targets[name]
            save_wol_targets(targets)
            tgbot.reply_to(message, MSGS["wol_removed"].format(name=name),
                           reply_markup=build_wol_menu(), parse_mode="Markdown")
        else:
            tgbot.reply_to(message, MSGS["wol_not_found"].format(name=name),
                           reply_markup=build_wol_menu())
        return

    tgbot.reply_to(message, MSGS["welcome"], reply_markup=build_main_menu(), parse_mode="Markdown")


@tgbot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if chat_id != ADMIN_ID:
        return

    tgbot.answer_callback_query(call.id)

    if call.data == "back_main":
        tgbot.edit_message_text(MSGS["welcome"], chat_id, msg_id,
                                reply_markup=build_main_menu(), parse_mode="Markdown")
        return

    if call.data == "status":
        tgbot.edit_message_text(get_system_status(), chat_id, msg_id,
                                reply_markup=build_back_button(), parse_mode="Markdown")
        return

    if call.data == "docker":
        tgbot.edit_message_text(get_docker_status(), chat_id, msg_id,
                                reply_markup=build_back_button(), parse_mode="Markdown")
        return

    if call.data == "network":
        tgbot.edit_message_text(get_network_status(), chat_id, msg_id,
                                reply_markup=build_back_button(), parse_mode="Markdown")
        return

    if call.data == "vpn":
        tgbot.edit_message_text(get_wireguard_status(), chat_id, msg_id,
                                reply_markup=build_back_button(), parse_mode="Markdown")
        return

    if call.data == "wol_menu":
        tgbot.edit_message_text(MSGS["wol_title"], chat_id, msg_id,
                                reply_markup=build_wol_menu(), parse_mode="Markdown")
        return

    if call.data.startswith("wol_send_"):
        name = call.data[len("wol_send_"):]
        targets = load_wol_targets()
        mac = targets.get(name)
        if not mac:
            tgbot.edit_message_text(MSGS["wol_not_found"].format(name=name), chat_id, msg_id,
                                    reply_markup=build_wol_menu())
            return
        success, msg = send_wol(mac, WOL_INTERFACE)
        tgbot.edit_message_text(msg, chat_id, msg_id,
                                reply_markup=build_wol_menu(), parse_mode="Markdown")
        return

    if call.data == "wol_add":
        user_state[chat_id] = "wol_add_name"
        tgbot.edit_message_text(MSGS["wol_prompt_name"], chat_id, msg_id)
        return

    if call.data == "wol_remove":
        targets = load_wol_targets()
        if not targets:
            tgbot.edit_message_text(MSGS["wol_empty"], chat_id, msg_id,
                                    reply_markup=build_wol_menu())
            return
        user_state[chat_id] = "wol_remove"
        listing = "\n".join(f"• `{n}`" for n in targets.keys())
        tgbot.edit_message_text(MSGS["wol_prompt_remove"].format(devices=listing),
                                chat_id, msg_id, parse_mode="Markdown")
        return
