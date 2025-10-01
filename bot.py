import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
from collections import defaultdict

# 🔑 Вставьте сюда свой токен
API_TOKEN = "8406440473:AAHELuDr2lvSCwN74x8hl-sqsX4LdUUoyPk"

# Категории расходов
CATEGORIES = ["Еда", "Дом", "Аптека", "Квартира", "Шмот", "Кафе/Ресторан", "Авто", "Отдых"]

# Хранилище расходов (в памяти)
expenses = defaultdict(list)


# ---- Состояния ----
class ExpenseForm(StatesGroup):
    waiting_for_amount = State()


# ---- Клавиатура ----
def get_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat, callback_data=f"cat:{cat}") for cat in CATEGORIES[:4]],
            [InlineKeyboardButton(text=cat, callback_data=f"cat:{cat}") for cat in CATEGORIES[4:]],
            [
                InlineKeyboardButton(text="Расходы за месяц", callback_data="stats_month"),
                InlineKeyboardButton(text="Отмена", callback_data="cancel"),
            ],
        ]
    )
    return keyboard


# ---- Хэндлеры ----
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Выберите категорию или статистику за месяц:",
        reply_markup=get_keyboard()
    )


async def category_chosen(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split(":")[1]
    await state.update_data(category=category)
    await callback.message.answer(f"Введите сумму для категории «{category}»:")
    await state.set_state(ExpenseForm.waiting_for_amount)


async def amount_entered(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data["category"]
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("Введите число, например: 123.45")
        return

    expenses[category].append((amount, datetime.now()))
    await message.answer(f"Добавлено {amount} € в категорию «{category}» ✅")
    await state.clear()
    await message.answer("Выберите категорию или статистику:", reply_markup=get_keyboard())


async def show_stats(callback: types.CallbackQuery, state: FSMContext):
    now = datetime.now()
    total = 0
    report = "📊 Расходы за месяц:\n\n"
    for category, items in expenses.items():
        cat_sum = sum(amount for amount, date in items if date.month == now.month and date.year == now.year)
        if cat_sum > 0:
            report += f"— {category}: {cat_sum:.2f} €\n"
            total += cat_sum
    report += f"\nИтого: {total:.2f} €"
    await callback.message.answer(report)
    await state.clear()


async def cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Действие отменено ❌", reply_markup=get_keyboard())


# ---- Main ----
async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Команды
    dp.message.register(cmd_start, F.text == "/start")
    dp.callback_query.register(category_chosen, F.data.startswith("cat:"))
    dp.message.register(amount_entered, ExpenseForm.waiting_for_amount)
    dp.callback_query.register(show_stats, F.data == "stats_month")
    dp.callback_query.register(cancel, F.data == "cancel")

    print("Бот запущен ✅")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
