import os
import json
import requests
import telebot

BOT_TOKEN = "8608324154:AAGwUM_vWlBznqqB6sg7ov_NKTAMe3Yu3K8"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "مرحباً بك يا عمر! 🎮\n\n"
        "أرسل الكوكي المنسوخ بصيغة JSON لبدء فحص الحساب."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()

    # فحص ما إذا كان الميساج يحتوي على كود الكوكي JSON
    if "[" in text and "]" in text and '"name"' in text:
        try:
            # استخراج الجزء الخاص بالـ JSON فقط في حال وجود أسطر زائدة
            start_idx = text.find("[")
            end_idx = text.rfind("]") + 1
            json_str = text[start_idx:end_idx]

            cookies_list = json.loads(json_str)
            
            cookies_dict = {}
            for cookie in cookies_list:
                name = cookie.get("name")
                value = cookie.get("value")
                if name and value:
                    cookies_dict[str(name).strip()] = str(value).strip()

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Referer': 'https://kiosgamer.co.id/'
            }

            bot.reply_to(message, "⏳ جاري فحص الحساب واستخراج البيانات...")

            # رابط جلب بيانات اللاعب المباشر
            url = "https://kiosgamer.co.id/api/auth/player"
            response = requests.get(url, headers=headers, cookies=cookies_dict, timeout=10)

            if response.status_code == 200:
                data = response.json()
                nickname = data.get("nickname") or data.get("username") or "غير متوفر"
                account_id = data.get("open_id") or data.get("player_id") or "غير متوفر"
                region = cookies_dict.get("region", "CO.ID")

                res_msg = (
                    "✅ **تم فحص الحساب بنجاح!**\n\n"
                    f"👤 **اسم الحساب:** `{nickname}`\n"
                    f"🆔 **الـ ID:** `{account_id}`\n"
                    f"🌍 **المنطقة:** `{region}`\n"
                    "🔒 **حالة الجلسة:** نشطة 100%"
                )
                bot.reply_to(message, res_msg, parse_mode="Markdown")
            else:
                bot.reply_to(message, f"❌ فشل جلب البيانات من الموقع (رمز الاستجابة: {response.status_code})")

        except Exception as e:
            bot.reply_to(message, f"❌ حدث خطأ في قراءة الكوكي:\n`{str(e)}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "أهلاً بك! الرجاء إرسال كود الكوكي (JSON) الخاص بالحساب لبدء الفحص.")

if __name__ == "__main__":
    bot.infinity_polling()
