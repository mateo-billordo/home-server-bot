from telebot import types

from bot.config import ADMIN_ID, MSGS, load_wol_targets


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
        types.InlineKeyboardButton(MSGS["btn_wol"], callback_data="wol_menu"),
    )
    return markup


def build_wol_menu() -> types.InlineKeyboardMarkup:
    targets = load_wol_targets()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for name in targets:
        markup.add(types.InlineKeyboardButton(f"⚡ {name}", callback_data=f"wol_send_{name}"))
    markup.add(
        types.InlineKeyboardButton(MSGS["btn_wol_add"], callback_data="wol_add"),
        types.InlineKeyboardButton(MSGS["btn_wol_remove"], callback_data="wol_remove"),
    )
    markup.add(types.InlineKeyboardButton(MSGS["btn_back"], callback_data="back_main"))
    return markup


def build_back_button() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(MSGS["btn_back"], callback_data="back_main"))
    return markup
