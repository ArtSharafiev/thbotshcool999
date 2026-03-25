import pandas as pd
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

bot = Bot(token="")
dp = Dispatcher(bot)

df = pd.read_excel("schedule.xlsx")
df["Дни"] = df["Дни"].ffill()

days = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ"]

classes = [
    '1а', '1б', '1в',
    '2а', '2б', '2в',
    '3а', '3б', '3в',
    '4а', '4б', '4в',
    '5а', '5б', '5в',
    '6а', '6б', '6в',
    '7а', '7б', '7в',
    '8а', '8б', '8в',
    '9а', '9б', '9в',
    '10а', '10б',
    '11а', '11б',
]

class_teachers = {
    "1а": "Федорова Р.Р.",
    "1б": "Малкова О.П.",
    "1в": "Хрулькова И.Н.",
    "2а": "Харисов М.М.",
    "2б": "Онучина Ю.А.",
    "2в": "Левкович О.В.",
    "3а": "Плясина Е.В.",
    "3б": "Офимкина С.В.",
    "3в": "Храмова Л.Р.",
    "4а": "Былинкина И.А.",
    "4б": "Степанова И.Я.",
    "4в": "Смирнова С.А.",
    "5а": "Тюрина О.В.",
    "5б": "Чекункова Е.В.",
    "5в": "Хакимова Г.И.",
    "6а": "Карагузина Н.В.",
    "6б": "Иванова В.Л.",
    "6в": "Грачева Н.И.",
    "7а": "Коган О.Г.",
    "7б": "Щукина Е.П.",
    "7в": "Нургалиева Л.П.",
    "8а": "Камалеева Т.И.",
    "8б": "Каримова Ф.И.",
    "8в": "Симонова И.С.",
    "9а": "Анохина А.А.",
    "9б": "Кочнева Т.П.",
    "9в": "Гибадуллина Т.А.",
    "10а": "Байдина Н.В.",
    "10б": "Ахмадуллина Л.И.",
    "11а": "Шишкина Н.Ю.",
    "11б": "Хайруллина Э.В."
}

def translate_weather(desc):
    d = desc.lower()

    if "fog" in d:
        return "Туман"
    if "mist" in d:
        return "Дымка"
    if "patchy rain nearby" in d:
        return "Местами дождь"
    if "light rain" in d:
        return "Небольшой дождь"
    if "moderate rain" in d:
        return "Умеренный дождь"
    if "heavy rain" in d:
        return "Сильный дождь"
    if "patchy snow nearby" in d:
        return "Местами снег"
    if "light snow" in d:
        return "Небольшой снег"
    if "moderate snow" in d:
        return "Умеренный снег"
    if "heavy snow" in d:
        return "Сильный снег"
    if "thunder" in d:
        return "Гроза"
    if "overcast" in d:
        return "Пасмурно"
    if "partly cloudy" in d:
        return "Переменная облачность"
    if "cloudy" in d:
        return "Облачно"
    if "clear" in d:
        return "Ясно"
    if "sunny" in d:
        return "Солнечно"
    if "rain" in d:
        return "Дождь"
    if "snow" in d:
        return "Снег"

    return desc

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Расписание 📚", "Погода 🌦", "Классные руководители 👩‍🏫")
    await msg.answer("Привет!", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "Расписание 📚")
async def choose_class(msg: types.Message):
    await show_classes(msg)

async def show_classes(message_or_call_message):
    kb = InlineKeyboardMarkup(row_width=3)

    buttons = [
        InlineKeyboardButton(c, callback_data=f"class_{c}")
        for c in classes
    ]

    kb.add(*buttons)

    await message_or_call_message.answer("Выбери класс:", reply_markup=kb)

def get_schedule(class_name, day_index):
    day = days[day_index]

    day_rows = df[df["Дни"].astype(str).str.strip().str.lower() == day.lower()]

    text = f"📅 {day}\n🏫 Класс: {class_name}\n\n"

    for _, row in day_rows.iterrows():
        lesson = row["Уроки"]
        subject = row[class_name]

        if pd.notna(subject):
            text += f"{lesson}. {subject}\n"

    if text.strip() == f"📅 {day}\n🏫 Класс: {class_name}":
        text += "Классный руководитель не известен."

    return text

def schedule_keyboard(class_name, day_index):
    kb = InlineKeyboardMarkup(row_width=3)

    buttons = []

    if day_index > 0:
        buttons.append(InlineKeyboardButton("⬅️", callback_data=f"day_{class_name}_{day_index-1}"))

    buttons.append(InlineKeyboardButton("🔙 Назад", callback_data="back_to_classes"))

    if day_index < len(days) - 1:
        buttons.append(InlineKeyboardButton("➡️", callback_data=f"day_{class_name}_{day_index+1}"))

    kb.row(*buttons)
    return kb

@dp.callback_query_handler(lambda c: c.data.startswith("class_"))
async def open_schedule(call: types.CallbackQuery):
    class_name = call.data.split("_")[1]
    day_index = 0

    text = get_schedule(class_name, day_index)
    kb = schedule_keyboard(class_name, day_index)

    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("day_"))
async def change_day(call: types.CallbackQuery):
    _, class_name, day_index = call.data.split("_")
    day_index = int(day_index)

    if day_index < 0:
        day_index = 0
    if day_index > len(days) - 1:
        day_index = len(days) - 1

    text = get_schedule(class_name, day_index)
    kb = schedule_keyboard(class_name, day_index)

    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == "back_to_classes")
async def back_to_classes(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=3)

    buttons = [
        InlineKeyboardButton(c, callback_data=f"class_{c}")
        for c in classes
    ]

    kb.add(*buttons)

    await call.message.edit_text("Выбери класс:", reply_markup=kb)
    await call.answer()

def get_weather():
    url = "https://wttr.in/Kazan?format=j1"
    data = requests.get(url).json()

    temp = int(data["current_condition"][0]["temp_C"])
    desc = data["current_condition"][0]["weatherDesc"][0]["value"]

    return temp, translate_weather(desc)

def school_decision(temp, group):
    if group == "junior":
        return "❌ Можно не идти" if temp <= -25 else "✅ Идти в школу"

    if group == "middle":
        return "❌ Можно не идти" if temp <= -28 else "✅ Идти в школу"

    if group == "senior":
        return "❌ Можно не идти" if temp <= -30 else "✅ Идти в школу"

@dp.message_handler(lambda m: m.text == "Погода 🌦")
async def weather_menu(msg: types.Message):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Младший", callback_data="weather_junior"),
        InlineKeyboardButton("Средний", callback_data="weather_middle"),
        InlineKeyboardButton("Старший", callback_data="weather_senior")
    )

    await msg.answer("Выбери класс:", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "Классные руководители 👩‍🏫")
async def class_teacher_menu(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=3)

    buttons = [
        InlineKeyboardButton(c, callback_data=f"teacher_{c}")
        for c in classes
    ]

    kb.add(*buttons)

    await msg.answer("Выбери класс:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("teacher_"))
async def teacher_result(call: types.CallbackQuery):
    class_name = call.data.split("_")[1]
    teacher = class_teachers.get(class_name, "Классный руководитель не известен")

    text = f"👩‍🏫 Классный руководитель\n🏫 Класс: {class_name}\n\n{teacher}"

    await call.message.edit_text(text)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("weather_"))
async def weather_result(call: types.CallbackQuery):
    group = call.data.split("_")[1]

    temp, desc = get_weather()
    decision = school_decision(temp, group)

    text = f"""🌦 Погода в Казани
🌡 Температура: {temp}°C
☁️ {desc}

{decision}"""

    await call.message.edit_text(text)
    await call.answer()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
