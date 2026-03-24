import pandas as pd
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

bot = Bot(token="8669987183:AAG299xorhTKIxwqf_nC3eaU-fCHFwZBCIM")
dp = Dispatcher(bot)

df = pd.read_excel("schedule.xlsx")
df["Дни"] = df["Дни"].ffill()

days = ["ПН", "ВТ", "СР", "ЧТ", "ПТ"]

classes = list(df.columns[2:])

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📚 Расписание", "🌦 Погода")

    await msg.answer("Привет!", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "📚 Расписание")
async def choose_class(msg: types.Message):

    kb = InlineKeyboardMarkup(row_width=3)

    buttons = [
        InlineKeyboardButton(c, callback_data=f"class_{c}")
        for c in classes
    ]

    kb.add(*buttons)

    await msg.answer("Выбери класс:", reply_markup=kb)

def get_schedule(class_name, day_index):

    day = days[day_index]
    day_rows = df[df["Дни"] == day]

    text = f"📅 {day}\n\n"

    for _, row in day_rows.iterrows():

        lesson = row["Уроки"]
        subject = row[class_name]

        if pd.notna(subject):
            text += f"{lesson}. {subject}\n"

    return text

@dp.callback_query_handler(lambda c: c.data.startswith("class_"))
async def open_schedule(call: types.CallbackQuery):

    class_name = call.data.split("_")[1]
    day_index = 0

    text = get_schedule(class_name, day_index)

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("⬅️", callback_data=f"day_{class_name}_{day_index-1}"),
        InlineKeyboardButton("➡️", callback_data=f"day_{class_name}_{day_index+1}")
    )

    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("day_"))
async def change_day(call: types.CallbackQuery):

    _, class_name, day_index = call.data.split("_")
    day_index = int(day_index)

    if day_index < 0:
        day_index = 0
    if day_index > len(days) - 1:
        day_index = len(days) - 1

    text = get_schedule(class_name, day_index)

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("⬅️", callback_data=f"day_{class_name}_{day_index-1}"),
        InlineKeyboardButton("➡️", callback_data=f"day_{class_name}_{day_index+1}")
    )

    await call.message.edit_text(text, reply_markup=kb)

def get_weather():

    url = "https://wttr.in/Kazan?format=j1"
    data = requests.get(url).json()

    temp = int(data["current_condition"][0]["temp_C"])
    desc = data["current_condition"][0]["weatherDesc"][0]["value"]

    return temp, desc

def school_decision(temp, group):

    if group == "junior":
        return "❌ Можно не идти" if temp <= -25 else "✅ Идти в школу"

    if group == "middle":
        return "❌ Можно не идти" if temp <= -28 else "✅ Идти в школу"

    if group == "senior":
        return "❌ Можно не идти" if temp <= -30 else "✅ Идти в школу"

@dp.message_handler(lambda m: m.text == "🌦 Погода")
async def weather_menu(msg: types.Message):

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("👶 Младшие", callback_data="weather_junior"),
        InlineKeyboardButton("🧑 Средние", callback_data="weather_middle"),
        InlineKeyboardButton("🎓 Старшие", callback_data="weather_senior")
    )

    await msg.answer("Выбери категорию:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("weather_"))
async def weather_result(call: types.CallbackQuery):

    group = call.data.split("_")[1]

    temp, desc = get_weather()
    decision = school_decision(temp, group)

    text = f"""
🌦 Погода в Казани

🌡 Температура: {temp}°C
☁️ {desc}

{decision}
"""

    await call.message.edit_text(text)

if __name__ == "__main__":
    executor.start_polling(dp)