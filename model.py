import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import telegram
from telegram import Update
import asyncio
from NST_TF import NST
import uvicorn

load_dotenv()
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Your render app URL + /webhook

app = FastAPI()
bot = telegram.Bot(token=TOKEN)
user_data = {}
model = NST()

async def start(update: Update):
    id = update.effective_user.id
    chat_id = update.effective_chat.id
    name = update.effective_user.username
    name = name if name != None else "there"
    user_data[id] = {"Content": None, "Style": None, "ChatID": chat_id}
    
    await bot.send_message(
        chat_id=chat_id,
        text=f"""**Hello {name}!**
                                    
To begin, please send me a **Content Image**""",
        parse_mode="Markdown"
    )

async def help_command(update: Update):
    chat_id = update.effective_chat.id
    await bot.send_message(
        chat_id=chat_id,
        text="**Neural Style Transfer Bot Help Guide**\n\n"
        "This bot lets you blend the *style* of one image with the *content* of another using AI.\n\n"
        "**How to use:**\n"
            "1. Type /start to begin.\n"
            "2. Send a **Content Image** (what you want to stylize).\n"
            "3. Then send a **Style Image** (the look you want to apply).\n"
            "4. Wait a few seconds, and get your new stylized image!\n\n"
        "**Tips:**\n"
            "- Larger images take more time and memory.\n"
            "- Try different combinations to get creative results.\n"
            "- You can restart anytime by sending a new content image.\n\n",
        parse_mode="Markdown"
    )

async def about_command(update: Update):
    chat_id = update.effective_chat.id
    await bot.send_message(
        chat_id=chat_id,
        text="<b>About Neural Style Transfer Bot</b>\n\n"
        "This bot uses <b>Neural Style Transfer</b> to blend the style of one image "
        "with the content of another, creating unique artistic visuals.\n\n"
        "Developed by Shudharshan P\n\n"
        "🔗 LinkedIn: www.linkedin.com/in/shudharshan-p-54546a315\n"
        "💻 GitHub: https://github.com/Shudharshan07/NST_API.git\n\n"
        "Feel free to connect, contribute, or report issues!",
        parse_mode="HTML"
    )

async def handle_image(update: Update):
    id = update.effective_user.id
    chat_id = update.effective_chat.id
    img = update.message.photo[-1]

    try:
        file = await bot.get_file(img.file_id)
        byt = bytes(await file.download_as_bytearray())

        if id not in user_data:
            user_data[id] = {"Content": None, "Style": None, "ChatID": chat_id}

        if user_data[id]["Content"] is None:
            user_data[id]["Content"] = byt
            await bot.send_message(
                chat_id=chat_id,
                text="Nice! Now send me a **Style Image**",
                parse_mode="Markdown"
            )

        elif user_data[id]["Style"] is None:
            user_data[id]["Style"] = byt
            await bot.send_message(
                chat_id=chat_id,
                text="Processing your image... Please wait ⏳"
            )
            
            try:
                print(f"Starting NST processing for user {id}")
                output = model(user_data[id]["Content"], user_data[id]["Style"])
                print(f"NST processing completed for user {id}")
                
                await bot.send_photo(chat_id=chat_id, photo=output)
                await bot.send_message(
                    chat_id=chat_id,
                    text="**Done!**\n\nSend a new **Content Image** to start again!",
                    parse_mode="Markdown"
                )
                
                # Reset for next round, but keep user in system
                user_data[id] = {"Content": None, "Style": None, "ChatID": chat_id}
                
            except ValueError as ve:
                print(f"❌ ValueError in NST: {ve}")
                await bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(ve)}")
                user_data[id] = {"Content": None, "Style": None, "ChatID": chat_id}
            except Exception as e:
                print(f"❌ Exception in NST: {e}")
                await bot.send_message(chat_id=chat_id, text=f"❌ Error processing image: {str(e)}")
                user_data[id] = {"Content": None, "Style": None, "ChatID": chat_id}
        
        else:
            # Both slots filled, treat this as new content image
            user_data[id]["Content"] = byt
            user_data[id]["Style"] = None
            await bot.send_message(
                chat_id=chat_id,
                text="New content image received! Now send me a **Style Image**",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        print(f"❌ Error in handle_image: {e}")
        await bot.send_message(chat_id=chat_id, text=f"❌ Error handling image: {str(e)}")
        # Reset on error but keep user
        if id in user_data:
            user_data[id] = {"Content": None, "Style": None, "ChatID": chat_id}

async def cancel_command(update: Update):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if user_id in user_data:
        del user_data[user_id]
        await bot.send_message(chat_id=chat_id, text="Session canceled. Use /start to begin again.")
    else:
        await bot.send_message(chat_id=chat_id, text="No active session to cancel.")

async def process_update(update: Update):
    """Process incoming telegram update"""
    try:
        if update.message:
            if update.message.text:
                if update.message.text.startswith('/start'):
                    await start(update)
                elif update.message.text.startswith('/help'):
                    await help_command(update)
                elif update.message.text.startswith('/about'):
                    await about_command(update)
                elif update.message.text.startswith('/cancel'):
                    await cancel_command(update)
            elif update.message.photo:
                await handle_image(update)
    except Exception as e:
        print(f"Error processing update: {e}")

@app.get("/")
async def root():
    return {"message": "Neural Style Transfer Bot is running!"}

@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming webhook from Telegram"""
    try:
        json_data = await request.json()
        update = Update.de_json(json_data, bot)
        await process_update(update)
        return {"status": "ok"}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

@app.on_event("startup")
async def startup_event():
    """Set webhook when the app starts"""
    try:
        if WEBHOOK_URL:
            webhook_url = f"{WEBHOOK_URL}/webhook"
            await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
            print(f"✅ Webhook set to: {webhook_url}")
        else:
            print("⚠️ Warning: WEBHOOK_URL not set in environment variables")
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Remove webhook when the app shuts down"""
    try:
        await bot.delete_webhook()
        print("✅ Webhook removed")
    except Exception as e:
        print(f"❌ Error removing webhook: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
