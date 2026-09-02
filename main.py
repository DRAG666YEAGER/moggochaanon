import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8364731756:AAHl77m4YHAFb_6_9w5cbzzB0ZCa3jrDLW8"

# 🔑 СПИСОК ID АДМИНИСТРАТОРОВ (Замени 123456789 на свой реальный Telegram ID)
ADMIN_IDS = [
    123456789, 
]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

class Form(StatesGroup):
    waiting_for_ref_message = State()

# Кнопка отмены для пользователя
def get_cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_ref_send")]
    ])

# Клавиатура панели администратора
def get_admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Создать реф. ссылку", callback_data="gen_ref_link")]
    ])

# --- ОБРАБОТЧИК /START (Обычный + Deep Link) ---
@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()  # Сбрасываем прошлые состояния
    
    args = command.args
    
    # Если пользователь перешел по реферальной ссылке (например, /start ref_123456789)
    if args and args.startswith("ref_"):
        admin_id = args.split("ref_")[1]
        
        # Сохраняем target_admin_id в память FSM
        await state.update_data(target_admin_id=admin_id)
        await state.set_state(Form.waiting_for_ref_message)
        
        await message.answer(
            "✉️ Вы перешли по персональной ссылке администратора.\n\n"
            "Напишите текст или отправьте медиа, и оно будет анонимно передано.\n"
            "Если передумали — нажмите кнопку ниже:",
            reply_markup=get_cancel_kb()
        )
        return

    # Если это обычный /start от админа или юзера
    if message.from_user.id in ADMIN_IDS:
        await message.answer(
            "👋 Привет, админ! Нажми кнопку ниже, чтобы получить свою реферальную ссылку.",
            reply_markup=get_admin_kb()
        )
    else:
        await message.answer("👋 Привет! Напишите нам через реферальные ссылки админов.")

# --- ГЕНЕРАЦИЯ ССЫЛКИ ДЛЯ АДМИНА ---
@router.callback_query(F.data == "gen_ref_link")
async def generate_ref_link(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{callback.from_user.id}"
    
    await callback.message.answer(
        f"🔗 **Ваша персональная реферальная ссылка:**\n\n`{ref_link}`\n\n"
        "Отправьте её пользователям. Сообщения, отправленные по ней, придут лично вам.",
        parse_mode="Markdown"
    )
    await callback.answer()

# --- ОТМЕНА ОТПРАВКИ СООБЩЕНИЯ ---
@router.callback_query(F.data == "cancel_ref_send")
async def cancel_ref_send(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await callback.answer("Нечего отменять.")
        return

    await state.clear()
    await callback.message.answer("❌ Отправка сообщения отменена.")
    await callback.answer()

# --- ПРИЕМ И ПЕРЕСЫЛКА СООБЩЕНИЯ АДМИНУ ---
@router.message(Form.waiting_for_ref_message)
async def process_ref_message(message: Message, state: FSMContext):
    data = await state.get_data()
    target_admin_id = data.get("target_admin_id")

    if not target_admin_id:
        await message.answer("⚠️ Ошибка: не найден получатель. Попробуйте перейти по ссылке снова.")
        await state.clear()
        return

    try:
        # Уведомляем админа и копируем сообщение юзера
        await bot.send_message(
            chat_id=target_admin_id,
            text="📨 **Новое анонимное сообщение по вашей ссылке:**"
        )
        await message.copy_to(chat_id=target_admin_id)

        await message.answer("✅ Ваше сообщение успешно отправлено!")
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения админу {target_admin_id}: {e}")
        await message.answer("❌ Не удалось доставить сообщение (возможно, админ заблокировал бота).")

    await state.clear()

async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
