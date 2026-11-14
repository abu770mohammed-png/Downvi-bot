import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# ضع توكن البوت الخاص بك هنا بين القوسين
TOKEN = "9273556837:AAGhKIFyq8W6-Fo9G6J3d6EEpXpmNTdxaKU"
bot = telebot.TeleBot(TOKEN)

# قاموس مؤقت لحفظ الروابط الخاصة بكل مستخدم
user_links = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "مرحباً بك في بوت تحميل الوسائط الشامل! 📥\n\n"
        "أرسل لي أي رابط (يوتيوب، تيك توك، إنستغرام، فيسبوك...) وسأقوم بتوفير خيارات التحميل لك."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: message.text and message.text.startswith('http'))
def handle_link(message):
    chat_id = message.chat.id
    url = message.text.strip()
    user_links[chat_id] = url
    
    # إنشاء الأزرار الشفافة (Inline Buttons)
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("📥 تحميل فيديو", callback_data="download_video"),
        InlineKeyboardButton("🎵 تحميل صوت (MP3)", callback_data="download_audio")
    )
    
    bot.send_message(chat_id, "🔗 تم استلام الرابط بنجاح.\nاختر الصيغة التي تريدها:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if chat_id not in user_links:
        bot.answer_callback_query(call.id, "❌ انتهت صلاحية الرابط، أرسل الرابط مجدداً.")
        return
    
    url = user_links[chat_id]
    bot.answer_callback_query(call.id, "جاري المعالجة، يرجى الانتظار...")
    bot.edit_message_text("⏳ جاري التحميل والرفع، قد يستغرق ذلك بعض الوقت حسب حجم الملف...", chat_id, call.message.message_id)

    os.makedirs('downloads', exist_ok=True)
    
    ydl_opts = {}
    if call.data == "download_video":
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
        }
    elif call.data == "download_audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if call.data == "download_audio":
                filename = os.path.splitext(filename)[0] + ".mp3"

        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            # قيود تيليجرام للبوتات العادية هي 50 ميجابايت كحد أقصى للرفع المباشر
            if file_size > 50 * 1024 * 1024:
                bot.send_message(chat_id, "❌ عذراً، حجم الملف كبير جداً (أكبر من 50 ميجابايت) ولا يمكنني إرساله.")
            else:
                with open(filename, 'rb') as f:
                    if call.data == "download_video":
                        bot.send_video(chat_id, f, caption="✨ تم التحميل بواسطة البوت بنجاح")
                    else:
                        bot.send_audio(chat_id, f, title=info.get('title', 'Audio'))
            
            # حذف الملف بعد إرساله لتوفير المساحة
            os.remove(filename)
        else:
            bot.send_message(chat_id, "❌ حدث خطأ أثناء معالجة الملف.")
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ:\n`{str(e)}`", parse_mode="Markdown")

if __name__ == '__main__':
    print("🤖 البوت يعمل الآن في الخلفية...")
    bot.infinity_polling()
