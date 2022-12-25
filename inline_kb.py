from aiogram import types

inl_button = [
 types.KeyboardButton(text="Рассылка"),
]

menu_button = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu_button.row(*inl_button)
