import os
from dotenv import load_dotenv
import telegram.ext
from NST_TF import NST

load_dotenv()
TOKEN = os.getenv("TOKEN")

model = NST()
user_data = {}

async def start(update, context):
    id = update.effective_user.id
    name = update.effective_user.username
    name = name if name != None else "there"
    user_data[id] = {"Content" : None, "Style" : None}
    
    await update.message.reply_text(f"""**Hello {name}!**
                                    
To begin, please send me a **Content Image**""", parse_mode="Markdown")
    
async def image(update, context):
    id = update.effective_user.id
    img = update.message.photo[-1]

    file = await context.bot.get_file(img.file_id)
    byt = bytes(await file.download_as_bytearray())


    if id not in user_data:
        user_data[id] = {"Content" : None, "Style" : None}

    if user_data[id]["Content"] is None:
        user_data[id]["Content"] = byt
        await update.message.reply_text("Nice, Now send me a **Style Image**", parse_mode="Markdown")

    elif user_data[id]["Style"] is None:
        user_data[id]["Style"] = byt
        await update.message.reply_text("Let me Start the Process...")
        
        try:
            output = model(user_data[id]["Content"], user_data[id]["Style"])
            await update.message.reply_photo(photo=output)
            await update.message.reply_text("Done!!")
            await update.message.reply_text("Now send me a **Style Image**", parse_mode="Markdown")
        except:
            await update.message.reply_text("Error processing image")

        del user_data[id]




app = telegram.ext.Application.builder().token(TOKEN).build()
app.add_handler(telegram.ext.CommandHandler('start', start))
app.add_handler(telegram.ext.MessageHandler(telegram.ext.filters.PHOTO, image))

app.run_polling(poll_interval=3)



# content 3 and style 9
# content 2 and style 15
# content 3 and style 15
# content 2 and style 16


