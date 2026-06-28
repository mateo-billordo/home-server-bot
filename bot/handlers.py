from bot.config import ADMIN_ID, MSGS, WOL_INTERFACE, tgbot, load_wol_targets, save_wol_targets
from bot.keyboards import build_main_menu, build_power_menu, build_back_button, build_vpn_buttons, build_shutdown_confirm
from bot.monitor import (
    get_system_status, get_docker_status, get_network_status,
    get_wireguard_status, send_wol, restart_wireguard, shutdown_device, normalize_mac,
)

# Multi-step flow state
user_state: dict[int, str] = {}
# Temp storage for multi-step add
user_data: dict[int, dict] = {}


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
    text = message.text.strip()

    if state == "power_add_name":
        user_data[chat_id] = {"name": text}
        user_state[chat_id] = "power_add_mac"
        tgbot.reply_to(message, MSGS["power_prompt_mac"])
        return

    if state == "power_add_mac":
        user_data[chat_id]["mac"] = normalize_mac(text)
        user_state[chat_id] = "power_add_host"
        tgbot.reply_to(message, MSGS["power_prompt_host"])
        return

    if state == "power_add_host":
        if text == "-":
            # No shutdown config
            data = user_data.pop(chat_id)
            targets = load_wol_targets()
            targets[data["name"]] = {"mac": data["mac"], "host": "", "user": ""}
            save_wol_targets(targets)
            tgbot.reply_to(message, MSGS["power_added"].format(name=data["name"]),
                           reply_markup=build_power_menu(), parse_mode="Markdown")
        else:
            user_data[chat_id]["host"] = text
            user_state[chat_id] = "power_add_user"
            tgbot.reply_to(message, MSGS["power_prompt_user"])
        return

    if state == "power_add_user":
        data = user_data.pop(chat_id)
        targets = load_wol_targets()
        targets[data["name"]] = {"mac": data["mac"], "host": data["host"], "user": text}
        save_wol_targets(targets)
        tgbot.reply_to(message, MSGS["power_added"].format(name=data["name"]),
                       reply_markup=build_power_menu(), parse_mode="Markdown")
        return

    if state == "power_remove":
        targets = load_wol_targets()
        if text in targets:
            del targets[text]
            save_wol_targets(targets)
            tgbot.reply_to(message, MSGS["power_removed"].format(name=text),
                           reply_markup=build_power_menu(), parse_mode="Markdown")
        else:
            tgbot.reply_to(message, MSGS["power_not_found"].format(name=text),
                           reply_markup=build_power_menu())
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
                                reply_markup=build_vpn_buttons(), parse_mode="Markdown")
        return

    if call.data == "vpn_restart":
        success, msg = restart_wireguard()
        tgbot.edit_message_text(msg, chat_id, msg_id,
                                reply_markup=build_vpn_buttons(), parse_mode="Markdown")
        return

    # --- Power menu ---
    if call.data == "power_menu":
        tgbot.edit_message_text(MSGS["power_title"], chat_id, msg_id,
                                reply_markup=build_power_menu(), parse_mode="Markdown")
        return

    if call.data.startswith("wake_"):
        name = call.data[5:]
        targets = load_wol_targets()
        info = targets.get(name)
        if not info or not info.get("mac"):
            tgbot.edit_message_text(MSGS["power_not_found"].format(name=name), chat_id, msg_id,
                                    reply_markup=build_power_menu())
            return
        success, result = send_wol(info["mac"], WOL_INTERFACE)
        if success:
            msg = MSGS["wol_success"].format(name=name, mac=result)
        else:
            msg = MSGS["wol_error"].format(error=result)
        tgbot.edit_message_text(msg, chat_id, msg_id,
                                reply_markup=build_power_menu(), parse_mode="Markdown")
        return

    if call.data.startswith("shutdown_") and not call.data.startswith("shutdown_yes_") and call.data != "shutdown_no":
        name = call.data[9:]
        targets = load_wol_targets()
        info = targets.get(name)
        if not info or not info.get("host"):
            tgbot.edit_message_text(MSGS["power_not_found"].format(name=name), chat_id, msg_id,
                                    reply_markup=build_power_menu())
            return
        tgbot.edit_message_text(
            MSGS["shutdown_confirm"].format(name=name, host=info["host"]),
            chat_id, msg_id,
            reply_markup=build_shutdown_confirm(name), parse_mode="Markdown")
        return

    if call.data.startswith("shutdown_yes_"):
        name = call.data[13:]
        targets = load_wol_targets()
        info = targets.get(name)
        if not info or not info.get("host"):
            tgbot.edit_message_text(MSGS["power_not_found"].format(name=name), chat_id, msg_id,
                                    reply_markup=build_power_menu())
            return
        success, error = shutdown_device(info["host"], info["user"])
        if success:
            msg = MSGS["shutdown_success"].format(name=name)
        else:
            msg = MSGS["shutdown_error"].format(name=name, error=error)
        tgbot.edit_message_text(msg, chat_id, msg_id,
                                reply_markup=build_power_menu(), parse_mode="Markdown")
        return

    if call.data == "shutdown_no":
        tgbot.edit_message_text(MSGS["shutdown_cancelled"], chat_id, msg_id,
                                reply_markup=build_power_menu(), parse_mode="Markdown")
        return

    if call.data == "power_add":
        user_state[chat_id] = "power_add_name"
        tgbot.edit_message_text(MSGS["power_prompt_name"], chat_id, msg_id)
        return

    if call.data == "power_remove":
        targets = load_wol_targets()
        if not targets:
            tgbot.edit_message_text(MSGS["power_empty"], chat_id, msg_id,
                                    reply_markup=build_power_menu())
            return
        user_state[chat_id] = "power_remove"
        listing = "\n".join(f"• `{n}`" for n in targets.keys())
        tgbot.edit_message_text(MSGS["power_prompt_remove"].format(devices=listing),
                                chat_id, msg_id, parse_mode="Markdown")
        return
