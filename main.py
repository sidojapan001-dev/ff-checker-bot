import os
import json
import requests
import telebot

# التوكن الجديد والنظيف الخاص بك
BOT_TOKEN = "8608324154:AAGwUM_vWlBznqqB6sg7ov_NKTAMe3Yu3K8"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "مرحباً بك يا عمر في بوت فحص حسابات فري فاير! 🎮\n\n"
        "أرسل الكوكي بصيغة JSON المنسوخ من Cookie-Editor لفحص الحساب واستخراج البيانات."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()

    # التحقق مما إذا كان النص المرسل عبارة عن JSON للكوكي
    if text.startswith("[") and text.endswith("]"):
        try:
            cookies_list = json.loads(text)
            
            # تحويل قائمة الكوكيز إلى Dictionary نظيف بدون رموز زائدة
            cookies_dict = {}
            for cookie in cookies_list:
                name = cookie.get("name")
                value = cookie.get("value")
                if name and value:
                    cookies_dict[str(name).strip()] = str(value).strip()

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
                'Origin': 'https://kiosgamer.co.id',
                'Referer': 'https://kiosgamer.co.id/?item=6659'
            }

            bot.reply_to(message, "⏳ جاري فحص الحساب واستخراج البيانات...")

            url = "https://kiosgamer.co.id/api/login"
            response = requests.get(url, headers=headers, cookies=cookies_dict, timeout=10)

            if response.status_code == 200:
                data = response.json()
                account_id = data.get("open_id") or data.get("account_id") or "غير متوفر"
                nickname = data.get("nickname") or data.get("name") or "غير متوفر"
                region = cookies_dict.get("region", "CO.ID")

                res_msg = (
                    "✅ **تم فحص الحساب بنجاح!**\n\n"
                    f"👤 **اسم الحساب:** `{nickname}`\n"
                    f"🆔 **الـ ID:** `{account_id}`\n"
                    f"🌍 **المنطقة:** `{region}`\n"
                    "🔒 **حالة الجلسة:** نشطة وشغالة 100%"
                )
                bot.reply_to(message, res_msg, parse_mode="Markdown")
            else:
                bot.reply_to(message, f"❌ فشل جلب البيانات من الموقع (رمز الاستجابة: {response.status_code})")

        except json.JSONDecodeError:
            bot.reply_to(message, "❌ خطأ في صيغة الـ JSON المبعوث. تأكد من نسخ الكوكي كاملاً عبر خيار Export JSON.")
        except Exception as e:
            bot.reply_to(message, f"❌ حدث خطأ غير متوقع:\n`{str(e)}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "أهلاً بك! الرجاء إرسال كود الكوكي (JSON) الخاص بالحساب لبدء الفحص.")

# تشغيل البوت
if __name__ == "__main__":
    bot.infinity_polling()
