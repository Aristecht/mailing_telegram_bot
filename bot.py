
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from config import Database

from inline_kb import menu_button
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import logging


TOKEN = '5698772626:AAE8yggXIj1JFtZxUO0MhhybHSdDUev2QEQ'
ADMIN = 5477105690

logging.basicConfig(level=logging.INFO)

class bot_mailing_class(StatesGroup):
    text = State()
    photo = State()
    state = State()


storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)
db = Database('database.db')

async def on_startup(_):
    print('Бот вышел в онлайн')

@dp.message_handler(commands=['start'])
async def start(message : Message):
    if message.from_user.id == ADMIN:
        await message.answer('Добро пожаловать в Админ-Панель! Выберите действие на клавиатуре', reply_markup=menu_button)
    else:
        if not db.user_exists(message.from_user.id):
            db.add_users(message.from_user.id)
        await message.answer('Приветствую тебя, сюда тебе будет приходить рассылка')

#==========================================================================================================
#Рассылка

@dp.message_handler(commands=['sendall'])
async def start(message : types.Message):
    if message.chat.type == 'private':
        if message.from_user.id == ADMIN:
            text = message.text[9:]
            users = db.get_users()
            for row in users:
                try:
                    await bot.send_message(row[0], text)
                    if int(row[1]) != 1:
                        db.set_active(row[0], 1)
                except:
                    db.set_active(row[0], 0)
            await bot.send_message(message.from_user.id, "Успешная рассылка")

@dp.message_handler(text='Рассылка')
async def start_mailing(message : Message):
    await message.answer(f'Введите текст рассылки:')
    await bot_mailing_class.text.set()

@dp.message_handler(state=bot_mailing_class.text)
async def mailing_text(message : Message, state: FSMContext):
    answer = message.text
    murkup = InlineKeyboardMarkup(row_width=2,
                                  inline_keyboard=[
                                      [
                                          InlineKeyboardButton(text='Добавить фотографию', callback_data='add_photo'),
                                          InlineKeyboardButton(text='Далее', callback_data='next'),
                                          InlineKeyboardButton(text='Отменить', callback_data='quit')
                                      ]
                                  ])
    await state.update_data(text=answer)
    await message.answer(text=answer, reply_markup=murkup)
    await bot_mailing_class.state.set()

@dp.callback_query_handler(text='next', state=bot_mailing_class.state)
async def start(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data.get('text')
    users = db.get_users()
    await state.finish()
    for row in users:
        print(users)
        try:
            await dp.bot.send_message(row[0], text=text)
            if int(row[1]) != 1:
                db.set_active(row[0], 1)
        except Exception:
            db.set_active(row[0], 0)
    await call.message.answer('Рассылка выполнена')

@dp.callback_query_handler(text='add_photo', state=bot_mailing_class.state)
async def add_photo(call: types.CallbackQuery):
    await call.message.answer(text='Пришлите фото')
    await bot_mailing_class.photo.set()

@dp.message_handler(state=bot_mailing_class.photo, content_types=types.ContentType.PHOTO)
async def mailing_text(message : Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo=photo_file_id)
    data = await state.get_data()
    text = data.get('text')
    photo = data.get('photo')
    markup = InlineKeyboardMarkup(row_width=2,
                                  inline_keyboard=[
                                      [
                                          InlineKeyboardButton(text='Далее', callback_data='next'),
                                          InlineKeyboardButton(text='Отменить', callback_data='quit'),
                                      ]
                                  ])
    await message.answer_photo(photo=photo, caption=text, reply_markup=markup)

@dp.callback_query_handler(text='next', state=bot_mailing_class.photo)
async def start(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data.get('text')
    photo = data.get('photo')
    await state.finish()
    users = db.get_users()
    for row in users:
        try:
            await dp.bot.send_photo(row[0], photo=photo, caption=text)
            if int(row[1]) != 1:
                db.set_active(row[0], 1)
        except Exception:
            db.set_active(row[0], 0)
    await call.message.answer('Рассылка выполнена')


@dp.message_handler(state=bot_mailing_class.photo)
async def no_photo(message: Message):
    murkup = InlineKeyboardMarkup(row_width=2,
                                  inline_keyboard=[
                                      [
                                          InlineKeyboardButton(text='Отменить', callback_data='quit')
                                      ]
                                  ])
    await message.answer('Пришли мне фотографию', reply_markup=murkup)

@dp.callback_query_handler(text='quit', state=[bot_mailing_class.text, bot_mailing_class.photo, bot_mailing_class.state])
async def quit(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer('Рассылка отменена')

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
