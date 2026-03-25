import pandas as pd
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text

bot = Bot(token="ТВОЙ_ТОКЕН")
dp = Dispatcher(bot)

df = pd.read_excel("schedule.xlsx")
df["Дни"] = df["Дни"].ffill()

days = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ"]

classes = [
    '1а','1б','1в','2а','2б','2в','3а','3б','3в',
    '4а','4б','4в','5а','5б','5в','6а','6б','6в',
    '7а','7б','7в','8а','8б','8в','9а','9б','9в',
    '10а','10б','11а','11б'
]

class_teachers = {
    "1а": "Федорова Р.Р.","1б": "Малкова О.П.","1в": "Хрулькова И.Н.",
    "2а": "Харисов М.М.","2б": "Онучина Ю.А.","2в": "Левкович О.В.",
    "3а": "Плясина Е.В.","3б": "Офимкина С.В.","3в": "Храмова Л.Р.",
    "4а": "Былинкина И.А.","4б": "Степанова И.Я.","4в": "Смирнова С.А.",
    "5а": "Тюрина О.В.","5б": "Чекункова Е.В.","5в": "Хакимова Г.И.",
    "6а": "Карагузина Н.В.","6б": "Иванова В.Л.","6в": "Грачева Н.И.",
    "7а": "Коган О.Г.","7б": "Щукина Е.П.","7в": "Нургалиева Л.П.",
    "8а": "Камалеева Т.И.","8б": "Каримова Ф.И.","8в": "Симонова И.С.",
    "9а": "Анохина А.А.","9б": "Кочнева Т.П.","9в": "Гибадуллина Т.А.",
    "10а": "Байдина Н.В.","10б": "Ахмадуллина Л.И.",
    "11а": "Шишкина Н.Ю.","11б": "Хайруллина Э.В."
}

def translate_weather(desc):
    d = desc.lower()
    if "fog" in d: return "Туман"
    if "rain" in d: return "Дождь"
    if "snow" in d: return "Снег"
    if "cloud" in d: return "Облачно"
    if "clear" in d or "sun" in d: return "Ясно"
    return desc

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Расписание 📚", "Погода 🌦", "Классные руководители 👩‍🏫")
    await msg.answer("Привет!", reply_markup=kb)

@dp.message_handler(Text(equals="Расписание 📚"))
async def choose_class(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(c, callback_data=f"class_{c}") for c in classes])
    await msg.answer("Выбери класс:", reply_markup=kb)

def get_schedule(class_name, day_index):
    day = days[day_index]
    rows = df[df["Дни"].astype(str).str.lower() == day.lower()]
    text = f"📅 {day}\n🏫 Класс: {class_name}\n\n"

    for _, row in rows.iterrows():
        subject = row[class_name]
        if pd.notna(subject):
            text += f"{row['Уроки']}. {subject}\n"

    return text

def schedule_keyboard(class_name, day_index):
    kb = InlineKeyboardMarkup()
    buttons = []

    if day_index > 0:
        buttons.append(InlineKeyboardButton("⬅️", callback_data=f"day_{class_name}_{day_index-1}"))

    buttons.append(InlineKeyboardButton("🔙 Назад", callback_data="back"))

    if day_index < len(days) - 1:
        buttons.append(InlineKeyboardButton("➡️", callback_data=f"day_{class_name}_{day_index+1}"))

    kb.row(*buttons)
    return kb

@dp.callback_query_handler(lambda c: c.data.startswith("class_"))
async def open_schedule(call: types.CallbackQuery):
    class_name = call.data.split("_")[1]
    day_index = 0
    await call.message.edit_text(get_schedule(class_name, day_index),
                                 reply_markup=schedule_keyboard(class_name, day_index))
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("day_"))
async def change_day(call: types.CallbackQuery):
    _, class_name, day_index = call.data.split("_")
    day_index = int(day_index)
    await call.message.edit_text(get_schedule(class_name, day_index),
                                 reply_markup=schedule_keyboard(class_name, day_index))
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == "back")
async def back(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(c, callback_data=f"class_{c}") for c in classes])
    await call.message.edit_text("Выбери класс:", reply_markup=kb)
    await call.answer()

@dp.message_handler(Text(equals="Погода 🌦"))
async def weather(msg: types.Message):
    data = requests.get("https://wttr.in/Kazan?format=j1").json()
    temp = int(data["current_condition"][0]["temp_C"])
    desc = translate_weather(data["current_condition"][0]["weatherDesc"][0]["value"])
    await msg.answer(f"🌦 Погода\n🌡 {temp}°C\n☁️ {desc}")

@dp.message_handler(Text(equals="Классные руководители 👩‍🏫"))
async def teachers(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(c, callback_data=f"teacher_{c}") for c in classes])
    await msg.answer("Выбери класс:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("teacher_"))
async def teacher(call: types.CallbackQuery):
    class_name = call.data.split("_")[1]
    teacher = class_teachers.get(class_name, "Классный руководитель не известен")
    await call.message.edit_text(f"🏫 {class_name}\n👩‍🏫 {teacher}")
    await call.answer()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
