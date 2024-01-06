import sqlite3
import logging
from aiogram import Bot, Dispatcher, types
import aiogram.contrib.middlewares.logging as LoggingMiddleware
from aiogram.utils import executor
from StableDiffusionAPI import RenderImage

TOKEN = ''
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())

welcome_message = """
Просто напишите текстовый запрос, и бот сгенерирует по нему изображение!
Просьба не спамить запросами, это приводит к визуальным багам чата!"""


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    async def welcome_():
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("♥️Steps♥️", callback_data='Steps')
        button2 = types.InlineKeyboardButton("♠️Ratio♠️", callback_data='Aspect_ratio')
        markup.add(button1, button2)
        await message.reply(welcome_message, reply_markup=markup)

    connect = sqlite3.connect('aurora.db')
    cursor = connect.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users_data(
            id TEXT PRIMARY KEY,
            prompt TEXT,
            steps INTEGER,
            height INTEGER,
            width INTEGER
        )""")
    connect.commit()

    people_id = message.from_user.username
    cursor.execute("SELECT id FROM users_data WHERE id = ?", (people_id,))
    data = cursor.fetchone()
    if data is None:
        user_data = (people_id, '', 20, 512, 512)
        cursor.execute("INSERT INTO users_data VALUES(?, ?, ?, ?, ?);", user_data)
        connect.commit()
        await welcome_()
    else:
        await welcome_()


@dp.callback_query_handler(lambda call: True)
async def button(call: types.CallbackQuery):
    async def back_():
        markup_ = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton("♥️Steps♥️", callback_data='Steps')
        item2 = types.InlineKeyboardButton("♠️Ratio♠️", callback_data='Aspect_ratio')
        markup_.add(item1, item2)
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text=welcome_message, reply_markup=markup_)

    if call.data == 'Steps':
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("20", callback_data="steps_20")
        button2 = types.InlineKeyboardButton("50", callback_data="steps_50")
        button3 = types.InlineKeyboardButton("100", callback_data="steps_100")
        button4 = types.InlineKeyboardButton("150", callback_data="steps_150")
        button5 = types.InlineKeyboardButton("⬅️", callback_data="back")
        markup.add(button1, button2, button3, button4, button5)
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Выберите желаемое кол-во итераций:", reply_markup=markup)
    elif call.data in ['steps_20', 'steps_50', 'steps_100', 'steps_150']:
        steps = int(call.data.split('_')[1])
        user_id = call.from_user.username  # Также используем username в качестве идентификатора пользователя
        connect = sqlite3.connect('aurora.db')
        cursor = connect.cursor()
        cursor.execute("UPDATE users_data SET steps = ? WHERE id = ?", (steps, user_id))
        connect.commit()
        await bot.answer_callback_query(call.id, f'Выбранное кол-во итераций - {steps}')
        await back_()
    elif call.data == 'Aspect_ratio':
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("16:9", callback_data="ratio_16:9")
        button2 = types.InlineKeyboardButton("3:2", callback_data="ratio_3:2")
        button3 = types.InlineKeyboardButton("1:1", callback_data="ratio_1:1")
        button4 = types.InlineKeyboardButton("2:3", callback_data="ratio_2:3")
        button5 = types.InlineKeyboardButton("9:16", callback_data="ratio_9:16")
        button6 = types.InlineKeyboardButton("⬅️", callback_data="steps_back")
        markup.add(button1, button2, button3, button4, button5, button6)
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Выберите желаемое соотношение сторон:", reply_markup=markup)

    elif call.data == 'back':
        await back_()


@dp.message_handler(content_types=['text'])
async def prompt_handler(message: types.Message):
    async def welcome_():
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("♥️Steps♥️", callback_data='Steps')
        button2 = types.InlineKeyboardButton("♠️Ratio♠️", callback_data='Aspect_ratio')
        markup.add(button1, button2)
        await message.reply(welcome_message, reply_markup=markup)

    user_id = message.from_user.username
    connect = sqlite3.connect('aurora.db')
    cursor = connect.cursor()
    cursor.execute("UPDATE users_data SET prompt = ? WHERE id = ?", (message.text, user_id))
    connect.commit()
    cursor.execute("SELECT prompt, steps, height, width FROM users_data WHERE id = ?", (user_id,))
    data = cursor.fetchone()
    if data is None:
        await message.reply("Пожалуйста, используйте команду /start, чтобы начать.")
        return

    prompt, steps, height, width = data

    message1 = await message.reply(f'Ваш запрос: <b>"{prompt}"</b> добавлен в очередь.\n'
                                   f'<b>Параметры запроса:</b>\n'
                                   f'<b>Steps: {steps}</b>\n'
                                   f'<b>Resolution: {width}x{height}</b>', parse_mode='html')
    message2 = await message.reply_sticker("CAACAgIAAxkBAAEJml5kpZHMSCQVPEFTLkjfYQrgZWXb3wACOhYAApQYyEvisP1oC-qPIy8E")
    image = RenderImage(prompt, steps, width, height)
    await bot.send_photo(message.chat.id, image, f"<b>Prompt:</b> {prompt}\n"
                                                 f"<b>Steps:</b> {str(steps)}\n"
                                                 f"<b>Resolution:</b> {str(width)}x{str(height)}", parse_mode='html')
    await bot.delete_message(message.chat.id, message1.message_id)
    await bot.delete_message(message.chat.id, message2.message_id)
    await welcome_()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)