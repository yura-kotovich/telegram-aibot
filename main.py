import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot("YOUR_TOKEN_HERE")   # ← заміни на свій токен

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_data[message.chat.id] = {"step": 1, "data": {"username": message.from_user.username or "Без юзернейму"}}
    
    text = """Привіт! Я працюю з обмеженою кількістю клієнтів, щоб гарантувати результат.

Перед нашою сесією прошу відповісти на 4 короткі питання. Це займе 1 хвилину, але дозволить мені підготувати конкретне рішення під ваш запит.

Вартість консультації: 500 грн/год. 👇"""
    
    bot.send_message(message.chat.id, text)
    ask_question(message.chat.id)

# ====================== ПИТАННЯ ======================
questions = {
    1: {
        "text": "Який напрямок ШІ вас цікавить найбільше?",
        "options": [
            "🎯 Інструменти та промптинг (стабільний результат)",
            "💻 AI для розробників (Cursor/Copilot)",
            "⚙️ Автоматизація та агенти (кастомні помічники)",
            "🖼️ Генерація контенту (Midjourney, Flux, відео)",
            "👤 В мене своє питання"
        ],
        "field": "direction"
    },
    2: {
        "text": "Який ваш поточний досвід роботи з нейромережами?",
        "options": [
            "🌱 Новачок (хочу стартувати правильно)",
            "⚡ Практик (є результат, але хаотичний)",
            "💼 Підприємець / Профі (шукаю автоматизацію)",
            "🗨 Не хочу вказувати"
        ],
        "field": "experience"
    },
    3: {
        "text": "Який формат розбору вашого кейсу для вас найзручніший?",
        "options": [
            "📲 Живий созвон",
            "📄 Текстовий розбір, інструкції, рішення"
        ],
        "field": "format"
    },
    4: {
        "text": "Опишіть ваше головне завдання або біль (опціонально).\n\n💡 Приклад: «Хочу автоматизувати звітність», «Cursor заплутався в коді» тощо.",
        "options": ["Пропустити"],
        "field": "comment"
    }
}

def ask_question(chat_id):
    step = user_data[chat_id]["step"]
    if step > 4:
        show_final(chat_id)
        return

    q = questions[step]
    markup = InlineKeyboardMarkup(row_width=1)
    for option in q["options"]:
        markup.add(InlineKeyboardButton(option, callback_data=option))

    bot.send_message(chat_id, q["text"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    step = user_data[chat_id]["step"]
    answer = call.data

    if step <= 4:
        field = questions[step].get("field")
        if field:
            user_data[chat_id]["data"][field] = answer if answer != "Пропустити" else "Пропущено"

    user_data[chat_id]["step"] += 1
    bot.answer_callback_query(call.id)
    ask_question(chat_id)

def show_final(chat_id):
    data = user_data[chat_id]["data"]
    username = data.get("username", "Без @username")
    
    final_text = """🎉 Дякую, заявку прийнято!
Я вже вивчаю ваші відповіді. Зв'яжуся з вами в особистих повідомленнях протягом 2 годин, щоб узгодити час сесії.

Якщо у вас терміновий запит, ви можете написати мені напряму: @yura_kotovich"""
    
    bot.send_message(chat_id, final_text)

    # Надсилання тобі в особистий чат
    result = f"""🔔 НОВА ЗАЯВКА!

👤 Username: @{username}
🎯 Напрямок: {data.get('direction', '—')}
📈 Досвід: {data.get('experience', '—')}
📞 Формат: {data.get('format', '—')}
📝 Кейс: {data.get('comment', '—')}"""

    try:
        bot.send_message(123456789, result)   # ← заміни 123456789 на ТВІЙ chat_id
    except:
        print("Не вдалося надіслати тобі")

bot.polling()
