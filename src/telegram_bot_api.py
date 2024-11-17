import nest_asyncio
nest_asyncio.apply()

from flask import Flask, request
from .gemini import Gemini
from md2tgmd import escape
from telegram.ext import ApplicationBuilder
from telegram import Update
from os import getenv
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
from .enums import TelegramBotCommands

load_dotenv()


app = Flask(__name__)




@app.get('/')
def hello_world():
    return 'Hello, World!'


@app.post('/webhook')
async def webhook():
    chat_id = None
    gemini = Gemini()

    telegram_app = ApplicationBuilder().token(getenv('TELEGRAM_BOT_TOKEN')).build()

    try:
        body = request.get_json()

        update = Update.de_json(body, telegram_app.bot)

        chat_id = update.message.chat_id

        if update.edited_message:
            return 'OK'
        else:
            message = await telegram_app.bot.send_message(chat_id=chat_id, text="Processing your request...")
            message_id = message.message_id

        if update.message.text == TelegramBotCommands.START:
            await telegram_app.bot.send_message(chat_id=chat_id, text="Welcome to Gemini Bot. Send me a message or an image to get started.")
            return 'OK'

        
        if update.message.photo:
            print('Generating images')
            file_id = update.message.photo[-1].file_id
            print(f"Images file id is {file_id}")
            file = await telegram_app.bot.get_file(file_id)
            print("Image file found")
            bytes_array = await file.download_as_bytearray()
            bytesIO = BytesIO(bytes_array)
            print("Images file as bytes")
            image = Image.open(bytesIO)
            print("Image opened")

            prompt = 'Describe the image'

            if update.message.caption:
                prompt = update.message.caption
            print("Prompt is ", prompt)

            text = gemini.send_image(prompt, image)

        else:
            print('Message')
            chat = gemini.get_model().start_chat()
            text = gemini.send_message(update.message.text, chat)
        
        await telegram_app.bot.edit_message_text(chat_id= chat_id, text=escape(text), message_id=message_id, parse_mode="MarkdownV2")
        return 'OK'
    except Exception as error:
        print(f"Error Occurred: {error}")
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": 'Sorry, I am not able to generate content for you right now. Please try again later. '
        }

async def send_message(chat_id, text):
    await telegram_app.bot.send_message(chat_id=chat_id, text=escape(text), parse_mode="MarkdownV2")
