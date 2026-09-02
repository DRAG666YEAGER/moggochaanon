import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Жестко прописываем токен, исключая проблемы с окружением на Bothost
BOT_TOKEN = "8364731756:AAHl77m4YHAFb_6_9w5cbzzB0ZCa3jrDLW8"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

class Form(StatesGroup):
    waiting_for_message = State()

def get_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Написать анонимно", callback_data="start_post")],
        [InlineKeyboardButton(text="ℹ️ О проекте / Правила", callback_data="about_bot")]
    ])

@router.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "👋 Привет! Это каркас бота анонимных сообщений.\n\n"
        "Выбери нужное действие в меню ниже:"
    )
    await message.answer(text, reply_markup=get_start_kb())

@router.callback_query(F.data == "start_post")
async def start_post(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 **[Режим заглушки]**\n"
        "Отправь любое сообщение (текст или фото), и бот покажет, что оно принято."
    )
    await state.set_state(Form.waiting_for_message)
    await callback.answer()

@router.callback_query(F.data == "about_bot")
async def about_bot(callback: CallbackQuery):
    await callback.message.answer(
        "ℹ️ **[Режим заглушки]**\n"
        "Здесь позже появятся правила публикации, информация о модерации и контакты админов.",
        reply_markup=get_start_kb()
    )
    await callback.answer()

@router.message(Form.waiting_for_message)
async def process_placeholder_message(message: Message, state: FSMContext):
    await message.answer(
        "✅ Сообщение успешно поймано ботом!\n"
        f"Тип контента: {'Текст' if message.text else 'Медиа'}\n\n"
        "Ждем подключения основного функционала от Gemini Pro 🚀",
        reply_markup=get_start_kb()
    )
    await state.clear()

async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    print("🤖 Бот запущен и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
