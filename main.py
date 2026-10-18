import asyncio
import logging
import aiohttp
from urllib.parse import parse_qs, urlparse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton, 
    CallbackQuery, LabeledPrice, PreCheckoutQuery
)

# التوكن النظيف الجديد الخاص بك
BOT_TOKEN = "8608324154:AAGwUM_vWlBznqqB6sg7ov_NKTAMe3Yu3K8"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class BotStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_token_check = State()
    waiting_for_token_email = State()

user_balances = {}
used_promo_codes = {}

PROMO_CODES = {
    "FREE30": {"reward": 30, "max_uses": 100, "current_uses": 0},
    "GIFT30": {"reward": 30, "max_uses": 100, "current_uses": 0},
    "WELCOME30": {"reward": 30, "max_uses": 100, "current_uses": 0},
    "VIP_OMAR": {"reward": 999999, "max_uses": 9999, "current_uses": 0, "is_vip": True},
    "VIP_AZIZ": {"reward": 999999, "max_uses": 9999, "current_uses": 0, "is_vip": True},
}

def get_user_balance(user_id):
    if user_id not in user_balances:
        user_balances[user_id] = 15
    return user_balances[user_id]

def parse_platform_info(user_input: str):
    primary_platform = "Google"
    if "facebook" in user_input.lower():
        primary_platform = "Facebook"
    elif "twitter" in user_input.lower() or "x.com" in user_input.lower():
        primary_platform = "Twitter (X)"
    elif "vk.com" in user_input.lower():
        primary_platform = "VKontakte"
    elif "apple" in user_input.lower():
        primary_platform = "Apple ID"
    return primary_platform

def get_main_reply_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="فحص الحسابات والخدمات")],
            [KeyboardButton(text="الرصيد والشحن"), KeyboardButton(text="نظام الربح")],
            [KeyboardButton(text="سجل حساباتي"), KeyboardButton(text="التعليمات والشروط")],
            [KeyboardButton(text="إعادة تشغيل البوت")]
        ],
        resize_keyboard=True
    )

def get_services_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="فحص ملف شخصي واسم الحساب (15 حجرة)", callback_data="buy_check_15")],
            [InlineKeyboardButton(text="كشف إيميل الاستعادة والروابط (60 حجرة)", callback_data="buy_email_60")]
        ]
    )

def get_recharge_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="شحن بـ 70 نجمة = 80 حجرة", callback_data="pay_stars")],
            [InlineKeyboardButton(text="شحن بـ 0.75$ USDT = 80 حجرة", callback_data="pay_usdt")]
        ]
    )

def get_earn_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="تسجيل الدخول اليومي (+3)", callback_data="daily_bonus")],
            [InlineKeyboardButton(text="دعوة صديق (+10)", callback_data="invite_friend")],
            [InlineKeyboardButton(text="استبدال رمز هدية (Promo Code)", callback_data="promo_redeem")]
        ]
    )

@dp.message(F.text == "إعادة تشغيل البوت")
@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext = None):
    if state:
        await state.clear()
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    welcome_text = (
        f"أهلاً بك يا {message.from_user.first_name} في بوت الفحص والخدمات الحقيقية!\n\n"
        f"حصلت على هدية ترحيبية: 15 حجرة\n"
        f"رصيدك الحالي: {balance} حجرة\n\n"
        "اختر ما تريد من القائمة أدناه:"
    )
    await message.answer(welcome_text, reply_markup=get_main_reply_keyboard())

@dp.message(F.text == "فحص الحسابات والخدمات")
async def services_menu(message: types.Message):
    await message.answer("اختر الخدمة المطلوبة للشراء والفحص:", reply_markup=get_services_keyboard())

@dp.message(F.text == "الرصيد والشحن")
async def recharge_menu(message: types.Message):
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    await message.answer(
        f"قسم الرصيد والشحن:\n\nرصيدك الحالي: {balance} حجرة\n\nاختر طريقة الشحن المناسبة:", 
        reply_markup=get_recharge_keyboard()
    )

@dp.message(F.text == "نظام الربح")
async def earn_menu(message: types.Message):
    await message.answer("نظام الربح والمكافآت:\n\nاكسب الحجارة مجاناً يومياً عبر الأزرار التالية:", reply_markup=get_earn_keyboard())

@dp.message(F.text == "سجل حساباتي")
async def history_menu(message: types.Message):
    await message.answer("سجل حساباتي:\n\n• لا توجد عمليات شراء معلقة.")

@dp.message(F.text == "التعليمات والشروط")
async def instructions_menu(message: types.Message):
    await message.answer("التعليمات والشروط:\n\n1- الخصم يتم فور تأكيد الشراء.\n2- أدخل اسم حساب اللعبة أو الـ Session Cookie بالطريقة المطلوبة.")

@dp.callback_query(F.data == "buy_check_15")
async def confirm_check_buy(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = get_user_balance(user_id)
    if balance < 15:
        await callback.answer("رصيدك غير كافٍ! تحتاج إلى 15 حجرة.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="تأكيد الخصم (15 حجرة)", callback_data="do_check_deduct")],
            [InlineKeyboardButton(text="إلغاء العملية", callback_data="cancel_action")]
        ]
    )
    await callback.answer()
    await callback.message.answer(f"تأكيد فحص ملف شخصي واسم الحساب (15 حجرة):\nرصيدك بعد الخصم: {balance - 15} حجرة", reply_markup=keyboard)

@dp.callback_query(F.data == "buy_email_60")
async def confirm_email_buy(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = get_user_balance(user_id)
    if balance < 60:
        await callback.answer("رصيدك غير كافٍ! تحتاج إلى 60 حجرة.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="تأكيد الخصم (60 حجرة)", callback_data="do_email_deduct")],
            [InlineKeyboardButton(text="إلغاء العملية", callback_data="cancel_action")]
        ]
    )
    await callback.answer()
    await callback.message.answer(f"تأكيد كشف إيميل الاستعادة والروابط (60 حجرة):\nرصيدك بعد الخصم: {balance - 60} حجرة", reply_markup=keyboard)

@dp.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery):
    await callback.answer("تم إلغاء العملية.", show_alert=True)
    await callback.message.delete()

@dp.callback_query(F.data == "do_check_deduct")
async def execute_check_deduction(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_balances[user_id] < 15:
        await callback.answer("رصيدك غير كافٍ!", show_alert=True)
        return
    user_balances[user_id] -= 15
    await callback.answer("تم خصم 15 حجرة!", show_alert=True)
    await state.set_state(BotStates.waiting_for_token_check)
    await callback.message.edit_text(
        f"تم خصم 15 حجرة.\nرصيدك المتبقي: {user_balances[user_id]} حجرة\n\n"
        "أرسل الآن اسم حساب اللعبة (In-Game Name) أو الـ Cookie للفحص:"
    )

@dp.callback_query(F.data == "do_email_deduct")
async def execute_email_deduction(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_balances[user_id] < 60:
        await callback.answer("رصيدك غير ك
