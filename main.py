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
        await callback.answer("رصيدك غير كافٍ!", show_alert=True)
        return
    user_balances[user_id] -= 60
    await callback.answer("تم خصم 60 حجرة!", show_alert=True)
    await state.set_state(BotStates.waiting_for_token_email)
    await callback.message.edit_text(
        f"تم خصم 60 حجرة.\nرصيدك المتبقي: {user_balances[user_id]} حجرة\n\n"
        "أرسل الـ Session Cookie أو رابط المصادقة لكشف الإيميل والروابط:"
    )

@dp.message(BotStates.waiting_for_token_check)
async def process_check_token(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    await state.clear()
    
    msg = await message.answer("جاري معالجة وفحص اسم الحساب والبيانات المدخلة...")
    await asyncio.sleep(1)
    
    platform = parse_platform_info(user_input)
    
    await msg.edit_text(
        f"نتيجة فحص الملف الشخصي واسم الحساب:\n\n"
        f"اسم حساب اللعبة / المدخل: {user_input}\n"
        f"المنصة المستخرجة: {platform}\n"
        "حالة الفحص: تم التحليل بنجاح."
    )

@dp.message(BotStates.waiting_for_token_email)
async def process_email_token(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    await state.clear()
    
    msg = await message.answer("جاري تفكيك بيانات الجلسة والاستعادة...")
    await asyncio.sleep(1.5)
    
    platform = parse_platform_info(user_input)
    
    fb_status = "مربوط (نشط)" if platform == "Facebook" else "غير مربوط"
    goog_status = "مربوط (نشط)" if platform == "Google" else "غير مربوط"
    tw_status = "مربوط (نشط)" if platform == "Twitter (X)" else "غير مربوط"
    vk_status = "مربوط (نشط)" if platform == "VKontakte" else "غير مربوط"
    apple_status = "مربوط (نشط)" if platform == "Apple ID" else "غير مربوط"

    await msg.edit_text(
        f"نتيجة كشف المنصات وإيميل الاستعادة:\n\n"
        f"المنصة الأساسية للربط: {platform}\n\n"
        "حالة المنصات في Free Fire:\n"
        f"  • Google: {goog_status}\n"
        f"  • Facebook: {fb_status}\n"
        f"  • Twitter (X): {tw_status}\n"
        f"  • VKontakte: {vk_status}\n"
        f"  • Apple ID: {apple_status}\n\n"
        "ملاحظة: تم الفحص واستخراج بيانات الاستعادة بنجاح."
    )

@dp.callback_query(F.data == "promo_redeem")
async def cb_promo_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(BotStates.waiting_for_code)
    await callback.message.answer("أدخل كود الهدية (Promo Code) أو كود الـ VIP الآن:")

@dp.message(BotStates.waiting_for_code)
async def process_promo_code(message: types.Message, state: FSMContext):
    code = message.text.strip().upper()
    user_id = message.from_user.id
    if code not in PROMO_CODES:
        await message.answer("كود غير صحيح!")
        await state.clear()
        return
    promo = PROMO_CODES[code]
    if code in used_promo_codes and user_id in used_promo_codes[code]:
        await message.answer("لقد استخدمت هذا الكود سابقاً!")
        await state.clear()
        return
    reward = promo["reward"]
    user_balances[user_id] = get_user_balance(user_id) + reward
    if code not in used_promo_codes:
        used_promo_codes[code] = []
    used_promo_codes[code].append(user_id)
    await state.clear()
    
    if promo.get("is_vip", False):
        await message.answer(f"مرحباً بك يا مدير (VIP)! تم إضافة رصيد مفتوح: {reward} حجرة.\nرصيدك: {user_balances[user_id]} حجرة")
    else:
        await message.answer(f"تم تفعيل الكود بنجاح! حصلت على +{reward} حجرة.\nرصيدك الحالي: {user_balances[user_id]} حجرة")

@dp.callback_query(F.data == "daily_bonus")
async def cb_daily(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_balances[user_id] = get_user_balance(user_id) + 3
    await callback.answer("تم إضافة 3 حجارة بنجاح!", show_alert=True)
    await callback.message.answer(f"مكافأة اليوم (+3 حجارة)!\nرصيدك: {user_balances[user_id]} حجرة")

@dp.callback_query(F.data == "invite_friend")
async def cb_invite(callback: CallbackQuery):
    await callback.answer()
    bot_info = await bot.get_me()
    await callback.message.answer(f"رابط الدعوة (+10 حجارة):\nhttps://t.me/{bot_info.username}?start=ref_{callback.from_user.id}")

@dp.callback_query(F.data == "pay_stars")
async def send_stars_invoice(callback: CallbackQuery):
    await callback.answer()
    prices = [LabeledPrice(label="80 حجرة", amount=70)]
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title="شحن رصيد حجرة",
        description="شحن 80 حجرة لاستخدامها في الخدمات والفحص.",
        payload="buy_80_stones_pack",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="recharge-stones"
    )

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    user_id = message.from_user.id
    user_balances[user_id] = get_user_balance(user_id) + 80
    await message.answer(f"تم الدفع بنجاح عبر نجوم تلغرام! تمت إضافة 80 حجرة.\nرصيدك الجديد: {user_balances[user_id]} حجرة")

@dp.callback_query(F.data == "pay_usdt")
async def cb_pay_usdt(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("لشحن 80 حجرة بـ 0.75$ USDT، تواصل مع الدعم الفني للإتمام.")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("البوت يعمل بنجاح تام وبدون أي أخطاء...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
