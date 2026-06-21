from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatAction
from aiohttp import web
from html import escape
import os
import asyncio
import logging
import random

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не встановлено в Environment Variables на Render!")
if not ADMIN_CHAT_ID:
    raise ValueError("❌ ADMIN_CHAT_ID не встановлено в Environment Variables на Render!")

ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)

user_states = {}


def get_welcome_text(first_name: str) -> str:
    return f"""Привіт, {escape(first_name)}!

Штучний інтелект може економити години роботи, а може заплутати ще більше. Моє завдання - допомогти вам впровадити ШІ без стресу та зайвих дій.

Дайте відповідь на 4 питання, я проаналізую ваш запит, щоб запропонувати конкретне рішення під ваш бюджет і задачі."""


QUESTION_1 = {
    "text": "Який напрямок ШІ вас цікавить найбільше? 👇",
    "options": [
        ("🎯 Інструменти та промптинг (стабільний результат)", "Інструменти та промптинг"),
        ("💻 AI для розробників (Cursor/Copilot)", "AI для розробників"),
        ("⚙️ Автоматизація та агенти (кастомні помічники)", "Автоматизація та агенти"),
        ("🖼️ Генерація контенту (Midjourney, Flux, відео)", "Генерація контенту"),
        ("👤 В мене своє питання", "Своє питання"),
    ]
}

QUESTION_2 = {
    "text": "Який ваш поточний досвід роботи з нейромережами? 👇",
    "options": [
        ("🌱 Новачок (хочу стартувати правильно)", "Новачок"),
        ("⚡ Практик (є результат, але хаотичний)", "Практик"),
        ("💼 Підприємець / Профі (шукаю автоматизацію)", "Підприємець/Профі"),
        ("🗨 Не хочу вказувати", "Не хочу вказувати"),
    ]
}

QUESTION_3 = {
    "text": "Який формат розбору вашого кейсу для вас найзручніший? 👇",
    "options": [
        ("📲 Живий созвон…", "Живий созвон"),
        ("📄 Текстовий розбір, інструкції, рішення", "Текстовий розбір"),
    ]
}

QUESTION_4_TEXT = "Опишіть ваше головне завдання або біль (опціонально).\n\n💡 Приклад: «Хочу автоматизувати звітність», «Cursor заплутався в коді», «Шукаю промпт». 👇"

FINAL_TEXT = """🎉 Дякую, заявку прийнято! Я вже вивчаю ваші відповіді.

Вартість індивідуального розбору вашого кейсу 500 грн/год. Зв'яжуся з вами в особистих повідомленнях протягом 2 год."""

AI_ANALYSIS_STEPS = [
    "🔍 Аналізую ваші відповіді...",
    "🎯 Визначаю напрямок задачі...",
    "🛠 Підбираю релевантні AI-інструменти...",
    "📊 Оцінюю формат та складність кейсу...",
    "✅ Формую персональні рекомендації...",
]

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(CommandStart())
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {
        "username": message.from_user.username or "Не вказано",
        "answers": {}
    }

    first_name = message.from_user.first_name or "друже"
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Почнемо? 👇", callback_data="start_quiz")]
    ])
    await message.answer(get_welcome_text(first_name), reply_markup=keyboard)


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
        await callback.answer("Сесія застаріла, натисніть /start")
        return

    data = callback.data
    state = user_states[user_id]
    await callback.answer()

    if data == "start_quiz":
        await show_question_1(callback.message)
    elif data in [v for _, v in QUESTION_1["options"]]:
        state["answers"]["напрямок_ШІ"] = data
        await show_question_2(callback.message)
    elif data in [v for _, v in QUESTION_2["options"]]:
        state["answers"]["досвід"] = data
        await show_question_3(callback.message)
    elif data in [v for _, v in QUESTION_3["options"]]:
        state["answers"]["формат"] = data
        await show_question_4(callback.message)


async def run_ai_analysis(message: types.Message):
    chat_id = message.chat.id

    # Спочатку короткий "бот друкує..." перед стартом аналізу
    await bot.send_chat_action(chat_id, ChatAction.TYPING)
    await asyncio.sleep(1.2)

    status_msg = await message.answer("🤖 AI аналізує ваш запит...")
    log_lines = []

    for step in AI_ANALYSIS_STEPS:
        # Перед кожним новим рядком знову показуємо "друкує...",
        # щоб виглядало як живий процес, а не просто таймер
        await bot.send_chat_action(chat_id, ChatAction.TYPING)
        await asyncio.sleep(random.uniform(0.6, 1.1))

        log_lines.append(f"✔ {step}")
        try:
            await status_msg.edit_text("\n".join(log_lines))
        except Exception:
            pass

    await asyncio.sleep(0.6)


@dp.message()
async def handle_text_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]["answers"]

    if ("напрямок_ШІ" in state and "досвід" in state and "формат" in state
            and "завдання_біль" not in state):
        state["завдання_біль"] = message.text

        await run_ai_analysis(message)
        await message.answer(FINAL_TEXT)
        await send_application_to_admin(user_id)
        del user_states[user_id]


async def send_application_to_admin(user_id):
    user_data = user_states.get(user_id)
    if not user_data:
        return

    answers = user_data["answers"]
    application_text = (
        f"📋 <b>НОВА ЗАЯВКА НА КОНСУЛЬТАЦІЮ</b>\n\n"
        f"👤 <b>Username:</b> @{user_data['username']}\n\n"
        f"1. Напрямок ШІ: {answers.get('напрямок_ШІ', 'Не вказано')}\n"
        f"2. Досвід: {answers.get('досвід', 'Не вказано')}\n"
        f"3. Формат: {answers.get('формат', 'Не вказано')}\n"
        f"4. Завдання/біль: {answers.get('завдання_біль', 'Не вказано')}"
    )

    try:
        await bot.send_message(ADMIN_CHAT_ID, application_text)
    except Exception as e:
        logging.error(f"Помилка відправки заявки: {e}")


async def health(request):
    return web.Response(text="Bot is running")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Веб-сервер запущено на порту {port}")


async def main():
    await start_web_server()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
