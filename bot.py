from aiogram import Bot, types
from aiogram import Dispatcher, F
from aiogram.filters import CommandStart
import os
import asyncio
import logging

# Логування для дебагу
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USERNAME = "yura_kotovich"  # без @

user_states = {}

WELCOME_TEXT = """Привіт! Я працюю з обмеженою кількістю клієнтів, щоб гарантувати результат.
Перед нашою сесією прошу відповісти на 4 короткі питання. Це займе 1 хвилину, але дозволить мені підготувати конкретне рішення під ваш запит.
Вартість консультації: 500 грн/год. 👇"""

QUESTION_1 = {
    "text": "Який напрямок ШІ вас цікавить найбільше?",
    "options": [
        ("🎯 Інструменти та промптинг (стабільний результат)", "Інструменти та промптинг"),
        ("💻 AI для розробників (Cursor/Copilot)", "AI для розробників"),
        ("⚙️ Автоматизація та агенти (кастомні помічники)", "Автоматизація та агенти"),
        ("🖼️ Генерація контенту (Midjourney, Flux, відео)", "Генерація контенту"),
        ("👤 В мене своє питання", "Своє питання")
    ]
}

QUESTION_2 = {
    "text": "Який ваш поточний досвід роботи з нейромережами?",
    "options": [
        ("🌱 Новачок (хочу стартувати правильно)", "Новачок"),
        ("⚡ Практик (є результат, але хаотичний)", "Практик"),
        ("💼 Підприємець / Профі (шукаю автоматизацію)", "Підприємець/Профі"),
        ("🗨 Не хочу вказувати", "Не хочу вказувати")
    ]
}

QUESTION_3 = {
    "text": "Який формат розбору вашого кейсу для вас найзручніший?",
    "options": [
        ("📲 Живий созвон…", "Живий созвон"),
        ("📄 Текстовий розбір, інструкції, рішення", "Текстовий розбір")
    ]
}

QUESTION_4_TEXT = "Опишіть ваше головне завдання або біль (опціонально).\n\n💡 Приклад: «Хочу автоматизувати звітність», «Cursor заплутався в коді», «Шукаю промпт»."

FINAL_TEXT = """🎉 Дякую, заявку прийнято!
Я вже вивчаю ваші відповіді. Зв'яжуся з вами в особистих повідомленнях протягом 2 годин, щоб узгодити час сесії.
Якщо у вас терміновий запит, ви можете написати мені напряму: @yura_kotovich"""

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

async def get_admin_chat_id():
    try:
        chat = await bot.get_chat(f"@{ADMIN_USERNAME}")
        return chat.id
    except Exception as e:
        logging.error(f"Не вдалося отримати chat_id адміна: {e}")
        return None

@dp.message(CommandStart())
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {
        "username": message.from_user.username or "Не вказано",
        "answers": {}
    }
    await message.answer(WELCOME_TEXT)
    await show_question_1(message)

async def show_question_1(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=text, callback_data=value)]
        for text, value in QUESTION_1["options"]
    ])
    await message.answer(QUESTION_1["text"], reply_markup=keyboard)

async def show_question_2(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=text, callback_data=value)]
        for text, value in QUESTION_2["options"]
    ])
    await message.answer(QUESTION_2["text"], reply_markup=keyboard)

async def show_question_3(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=text, callback_data=value)]
        for text, value in QUESTION_3["options"]
    ])
    await message.answer(QUESTION_3["text"], reply_markup=keyboard)

async def show_question_4(message: types.Message):
    await message.answer(QUESTION_4_TEXT)

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_states:
        await callback.answer("Сесія застаріла, почніть з /start")
        return

    data = callback.data
    state = user_states[user_id]

    await callback.answer()

    if data in [v for _, v in QUESTION_1["options"]]:
        state["answers"]["напрямок_ШІ"] = data
        await show_question_2(callback.message)
    elif data in [v for _, v in QUESTION_2["options"]]:
        state["answers"]["досвід"] = data
        await show_question_3(callback.message)
    elif data in [v for _, v in QUESTION_3["options"]]:
        state["answers"]["формат"] = data
        await show_question_4(callback.message)

@dp.message()
async def handle_text_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]["answers"]

    if ("напрямок_ШІ" in state and 
        "досвід" in state and 
        "формат" in state and 
        "завдання_біль" not in state):
        
        state["завдання_біль"] = message.text
        await message.answer(FINAL_TEXT)
        await send_application_to_admin(user_id)
        del user_states[user_id]

async def send_application_to_admin(user_id):
    user_data = user_states.get(user_id)
    if not user_data:
        return

    admin_chat_id = await get_admin_chat_id()
    if not admin_chat_id:
        logging.error("Не вдалося отримати chat_id адміна")
        return

    answers = user_data["answers"]
    application_text = f"""
📋 <b>НОВА ЗАЯВКА НА КОНСУЛЬТАЦІЮ</b>

👤 <b>Username:</b> @{user_data["username"]}

1. Напрямок ШІ: {answers.get("напрямок_ШІ", "Не вказано")}
2. Досвід: {answers.get("досвід", "Не вказано")}
3. Формат: {answers.get("формат", "Не вказано")}
4. Завдання/біль: {answers.get("завдання_біль", "Не вказано")}
"""

    try:
        await bot.send_message(admin_chat_id, application_text)
    except Exception as e:
        logging.error(f"Помилка відправки заявки: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
