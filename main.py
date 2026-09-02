import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Например: @my_town_podslushka или -1001234567890

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Состояния для FSM (машины состояний) при отправке секрета
class Form(StatesGroup):
    waiting_for_message = State()

# Клавиатура для старта
def get_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Написать анонимно", callback_data="start_post")]
    ])

# Команда /start
@router.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "👋 Привет! Это бот анонимных сообщений городского паблика.\n\n"
        "Все сообщения отправляются строго конфиденциально. "
        "Нажми кнопку ниже, чтобы отправить свою новость, историю или вопрос."
    )
    await message.answer(text, reply_markup=get_start_kb())

# Нажатие на кнопку начала отправки
@router.callback_query(F.data == "start_post")
async def start_post(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 Отправь текст, фото или видео, которые хочешь опубликовать. "
        "Оно будет передано модераторам / в канал анонимно."
    )
    await state.set_state(Form.waiting_for_message)
    await callback.answer()

# Получение сообщения от пользователя и пересылка в канал
@router.message(Form.waiting_for_message)
async def process_anonymous_message(message: Message, state: FSMContext):
    if not CHANNEL_ID:
        await message.answer("⚠️ Ошибка конфигурации: не указан ID канала.")
        await state.clear()
        return

    try:
        # Пересылаем контент в канал без автора
        # Метод copy_message аккуратно пересылает текст, фото, видео и т.д.
        sent_msg = await message.copy_to(
            chat_id=CHANNEL_ID,
            caption=f"💬 **Анонимное сообщение:**\n\n{message.caption or message.text or ''}" if message.text or message.caption else None
        )
        
        # Если это медиа без текста, добавляем заголовок отдельно или копируем как есть
        # Для простоты copy_message сохраняет оригинальный caption, 
        # поэтому можно просто добавить хэштег или вотермарку.
        
        await message.answer(
            "✅ Твое сообщение успешно отправлено на публикацию!",
            reply_markup=get_start_kb()
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке в канал: {e}")
        await message.answer("❌ Произошла ошибка при отправке. Попробуй позже.")

    await state.clear()

async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())