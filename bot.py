import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# 1. Credentials Setup
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Main Bot Client
app = Client(
    "otp_manager_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

USER_ACCOUNTS = {}  # {acc_id: {"client": client, "phone": phone, "name": name, "username": username, "session": session_string}}
USER_STATE = {}     # User ke current action ko track karne ke liye

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Login via Session", callback_data="add_login")],
        [InlineKeyboardButton("📂 Manage Accounts", callback_data="list_accounts")],
        [InlineKeyboardButton("🗑️ Delete Account", callback_data="delete_menu")]
    ])

# 2. /start Command Handler
@app.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    user_id = message.from_user.id
    USER_STATE.pop(user_id, None)
    await message.reply_text(
        "🚀 **Advanced OTP & Account Manager Bot**\n\n"
        "Welcome! Bot bilkul active hai. Niche diye gaye options ka use karein:",
        reply_markup=get_main_keyboard()
    )

# 3. Inline Buttons Handler
@app.on_callback_query()
async def callback_handler(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "add_login":
        USER_STATE[user_id] = "awaiting_session"
        await callback_query.message.edit_text(
            "🔑 **Session Login:**\n\n"
            "Kripya apna poora **Pyrogram v2 String Session** yahan bhejain:\n"
            "*(Dhyan rahe yeh Telethon ki string nahi honi chahiye)*",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="go_back")]])
        )

    elif data == "list_accounts":
        if not USER_ACCOUNTS:
            await callback_query.answer("⚠️ Abhi tak koi account add nahi kiya gaya hai!", show_alert=True)
            return

        buttons = []
        for acc_id, acc_data in USER_ACCOUNTS.items():
            buttons.append([InlineKeyboardButton(f"📱 +{acc_data['phone']} | {acc_data['name']}", callback_data=f"manage_acc_{acc_id}")])
        buttons.append([InlineKeyboardButton("« Back", callback_data="go_back")])

        await callback_query.message.edit_text(
            "📂 **Active Accounts Panel:**\n\nKisi bhi account ki details ya options ke liye us par click karein:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("manage_acc_"):
        acc_id = int(data.split("_")[2])
        if acc_id in USER_ACCOUNTS:
            acc = USER_ACCOUNTS[acc_id]
            text = (
                f"👤 **Account Details:**\n\n"
                f"• **Name:** {acc['name']}\n"
                f"• **Username:** @{acc['username'] if acc['username'] else 'None'}\n"
                f"• **Phone:** +{acc['phone']}\n"
                f"• **ID:** `{acc_id}`\n\n"
                f"Status: **Online & Listening for OTP 🟢**"
            )
            buttons = [
                [InlineKeyboardButton("📩 Check Latest OTP", callback_data=f"get_otp_{acc_id}")],
                [InlineKeyboardButton("📤 Export Session String", callback_data=f"exp_sess_{acc_id}")],
                [InlineKeyboardButton("« Back to Accounts", callback_data="list_accounts")]
            ]
            await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await callback_query.answer("❌ Account nahi mila.", show_alert=True)

    elif data.startswith("get_otp_"):
        acc_id = int(data.split("_")[2])
        if acc_id in USER_ACCOUNTS:
            acc = USER_ACCOUNTS[acc_id]
            try:
                last_msg = "Telegram (777000) se abhi tak koi message nahi mila."
                async for msg in acc["client"].get_chat_history(777000, limit=1):
                    if msg.text:
                        last_msg = msg.text
                
                await callback_query.message.edit_text(
                    f"📩 **Latest OTP for +{acc['phone']}:**\n\n{last_msg}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data=f"manage_acc_{acc_id}")]])
                )
            except Exception as e:
                await callback_query.answer(f"Error fetching OTP: {str(e)}", show_alert=True)

    elif data.startswith("exp_sess_"):
        acc_id = int(data.split("_")[2])
        if acc_id in USER_ACCOUNTS:
            session_str = USER_ACCOUNTS[acc_id]["session"]
            await callback_query.message.edit_text(
                f"📤 **Session String for +{USER_ACCOUNTS[acc_id]['phone']}:**\n\n`{session_str}`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data=f"manage_acc_{acc_id}")]])
            )

    elif data == "delete_menu":
        if not USER_ACCOUNTS:
            await callback_query.answer("⚠️ Delete karne ke liye koi account nahi hai!", show_alert=True)
            return

        buttons = []
        for acc_id, acc_data in USER_ACCOUNTS.items():
            buttons.append([InlineKeyboardButton(f"❌ Delete: +{acc_data['phone']}", callback_data=f"del_acc_{acc_id}")])
        buttons.append([InlineKeyboardButton("« Back", callback_data="go_back")])

        await callback_query.message.edit_text(
            "🗑️ **Delete Account Panel:**\n\nJis account ko remove karna ho us par click karein:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("del_acc_"):
        acc_id = int(data.split("_")[2])
        if acc_id in USER_ACCOUNTS:
            try:
                await USER_ACCOUNTS[acc_id]["client"].stop()
            except:
                pass
            del USER_ACCOUNTS[acc_id]
            await callback_query.answer("✅ Account successfully remove kar diya gaya!", show_alert=True)
            
            if USER_ACCOUNTS:
                buttons = []
                for a_id, a_data in USER_ACCOUNTS.items():
                    buttons.append([InlineKeyboardButton(f"❌ Delete: +{a_data['phone']}", callback_data=f"del_acc_{a_id}")])
                buttons.append([InlineKeyboardButton("« Back", callback_data="go_back")])
                await callback_query.message.edit_text("🗑️ **Delete Account Panel:**", reply_markup=InlineKeyboardMarkup(buttons))
            else:
                await callback_query.message.edit_text("👋 **Main Menu:**", reply_markup=get_main_keyboard())
        else:
            await callback_query.answer("❌ Account nahi mila.", show_alert=True)

    elif data == "go_back":
        USER_STATE.pop(user_id, None)
        await callback_query.message.edit_text(
            "👋 **Main Menu:**",
            reply_markup=get_main_keyboard()
        )

# 4. Text Message Handler (Session Input & Smart Validation)
@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_text_messages(client, message: Message):
    user_id = message.from_user.id
    state = USER_STATE.get(user_id)

    if state == "awaiting_session":
        session_string = message.text.strip()
        USER_STATE.pop(user_id, None)
        
        # Smart Check: Telethon string usually 1-2 character se start hoti hai ya alag length ki hoti hai
        if len(session_string) < 200:
            await message.reply_text(
                "❌ **Invalid Session String Length!**\n\n"
                "Aapne jo string di hai woh bahut choti hai. Pyrogram v2 string session lamba hota hai (~300+ characters). Kripya sahi Pyrogram string session bhejein.",
                reply_markup=get_main_keyboard()
            )
            return

        status_msg = await message.reply_text("⏳ Session verify ho raha hai, kripya intezaar karein...")

        try:
            user_client = Client(
                name=f"usr_{os.urandom(4).hex()}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=session_string,
                in_memory=True
            )
            await user_client.start()
            me = await user_client.get_me()

            USER_ACCOUNTS[me.id] = {
                "client": user_client,
                "phone": me.phone_number,
                "name": me.first_name,
                "username": me.username,
                "session": session_string
            }

            await status_msg.edit_text(
                f"✅ **Account Successfully Login Ho Gaya!**\n\n"
                f"👤 **Name:** {me.first_name}\n"
                f"🆔 **ID:** `{me.id}`\n"
                f"📱 **Phone:** +{me.phone_number}\n\n"
                f"Ab is account par aane wale sare OTPs is bot par auto-forward honge.",
                reply_markup=get_main_keyboard()
            )

            @user_client.on_message(filters.chat(777000))
            async def otp_listener(u_cli, otp_msg: Message):
                if otp_msg.text:
                    await client.send_message(
                        chat_id=user_id,
                        text=f"🚨 **New OTP Received!**\n\n📱 Account: `+{me.phone_number}`\n\n{otp_msg.text}"
                    )

        except Exception as e:
            error_text = str(e)
            if "unpack requires a buffer" in error_text or "string" in error_text.lower():
                err_msg = (
                    "❌ **Invalid Pyrogram Session Format!**\n\n"
                    "Aapne shayad **Telethon** ki string bhej di hai ya string ke beech mein koi space/character cut gaya hai.\n"
                    "Yeh bot sirf **Pyrogram v2 String Session** support karta hai."
                )
            else:
                err_msg = f"❌ **Login Fail Ho Gaya:**\n`{error_text}`"

            await status_msg.edit_text(
                err_msg,
                reply_markup=get_main_keyboard()
            )

# 5. Direct Bot Runner
if __name__ == "__main__":
    print("Starting bot directly...")
    app.run()
