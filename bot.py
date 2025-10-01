import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web
import sqlite3
import os

# Токен берём из переменной окружения
API_TOKEN = os.getenv("API_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ---------- Работа с базой ----------
DB_PATH = "expenses.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        amount REAL
    )
    """)
    conn.commit()
    conn.close()

def add_expense(category, amount):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (category, amount) VALUES (?, ?)", (category, amount))
    conn.commit()
    conn.close()

def get_total_expenses():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    data = cursor.fetchall()
    conn.close()
    return data

# ---------- Кнопки ----------
CATEGORIES = ["Еда", "Дом", "Аптека", "Квартира", "Шмот", "Кафе/Ресторан", "Авто", "Отдых", "Расходы за месяц", "Отмена"]

def get_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(text=cat, callback_data=cat) for cat in CATEGORIES]
    keyboard.add(*buttons)
    return keyboard

# ---------- Хэндлеры ----------
@dp.message()
async def handle_message(message: types.Message):
    await message.answer("Выберите категорию:", reply_markup=get_keyboard())

@dp.callback_query()
async def handle_callback(call: types.CallbackQuery):
    data = call.data
    if data == "Отмена":
        await call.message.answer("Операция отменена")
        return
    elif data == "Расходы за месяц":
        totals = get_total_expenses()
        if totals:
            text = "\n".join([f"{cat}: {amount} €" for cat, amount in totals])
        else:
            text = "Расходов нет"
        await call.message.answer(text)
    else:
        # Категория выбрана, ждём сумму
        await call.message.answer(f"Введите сумму для категории {data}:")
        # Сохраняем выбранную категорию в состоянии (можно доработать FSM)
        global current_category
        current_category = data

@dp.message()
async def handle_amount(message: types.Message):
    global current_category
    if current_category:
        try:
            amount = float(message.text.replace(",", "."))
            add_expense(current_category, amount)
            await message.answer(f"Добавлено {amount} € в категорию {current_category}")
        except ValueError:
            await message.answer("Неверная сумма. Введите число.")
        current_category = None

# ---------- HTTP сервер для Render ----------
async def on_startup(app):
    # Запускаем polling бота в фоне
    asyncio.create_task(dp.start_polling())

async def handle_root(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.on_startup.append(on_startup)
app.router.add_get("/", handle_root)

# ---------- Основной запуск ----------
if __name__ == "__main__":
    init_db()
    web.run_app(app, host="0.0.0.0", port=10000)
