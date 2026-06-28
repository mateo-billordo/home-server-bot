from telebot import types

from bot.config import MSGS, load_wol_targets


def build_main_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(MSGS["btn_status"], callback_data="status"),
        types.InlineKeyboardButton(MSGS["btn_docker"], callback_data="docker"),
    )
    markup.add(
        types.InlineKeyboardButton(MSGS["btn_network"], callback_data="network"),
        types.InlineKeyboardButton(MSGS["btn_vpn"], callback_data="vpn"),
    )
    markup.add(
        types.InlineKeyboardButton(MSGS["btn_power"], callback_data="power_menu"),
    )
    return markup


def build_power_menu() -> types.InlineKeyboardMarkup:
    targets = load_wol_targets()
    markup = types.InlineKeyboardMarkup(row_width=2)
    for name, info in targets.items():
        row = []
        if info.get("mac"):
            row.append(types.InlineKeyboardButton(
                f"⚡ {name}", callback_data=f"wake_{name}"))
        if info.get("host") and info.get("user"):
            row.append(types.InlineKeyboardButton(
                f"🔴 {name}", callback_data=f"shutdown_{name}"))
        if row:
            markup.add(*row)
    markup.add(
        types.InlineKeyboardButton(MSGS["power_btn_add"], callback_data="power_add"),
        types.InlineKeyboardButton(MSGS["power_btn_remove"], callback_data="power_remove"),
    )
    markup.add(types.InlineKeyboardButton(MSGS["btn_back"], callback_data="back_main"))
    return markup


def build_shutdown_confirm(name: str) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(MSGS["shutdown_btn_yes"], callback_data=f"shutdown_yes_{name}"),
        types.InlineKeyboardButton(MSGS["shutdown_btn_no"], callback_data="shutdown_no"),
    )
    return markup


def build_back_button() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(MSGS["btn_back"], callback_data="back_main"))
    return markup


def build_vpn_buttons() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(MSGS["btn_vpn_restart"], callback_data="vpn_restart"))
    markup.add(types.InlineKeyboardButton(MSGS["btn_back"], callback_data="back_main"))
    return markup
