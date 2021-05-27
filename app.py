'''
vaccine bot to help people get vaccinated.
'''

import re
import configparser
from flask import Flask, request
import telegram
from telegram import ReplyKeyboardMarkup, KeyboardButton,InlineKeyboardMarkup,InlineKeyboardButton



parser = configparser.ConfigParser()
parser.read('credentials/config.conf')




global bot
global TOKEN
TOKEN = parser['Telebot']['token']
URL = parser['Telebot']['URL']
bot = telegram.Bot(token=TOKEN)


app = Flask(__name__)

states = ['Andaman and Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chandigarh', 'Chhattisgarh', 'Dadra and Nagar Haveli', 'Daman and Diu', 'Delhi', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jammu and Kashmir', 'Jharkhand', 'Karnataka', 'Kerala', 'Ladakh', 'Lakshadweep', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Puducherry', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal']
District = []


@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    print(update)
    callback_query = update.callback_query
    if callback_query is not None:
        if callback_query.data == "state":
            reply_markup = ReplyKeyboardMarkup([states],resize_keyboard=True,one_time_keyboard=True)
            bot.sendMessage(chat_id=callback_data.from.id, text='Enter the state name', reply_markup=reply_markup,reply_to_message_id=callback_data.message.message_id)
        return 'ok'
    chat_id = update.message.chat.id
    msg_id = update.message.message_id

    # Telegram understands UTF-8, so encode text for unicode compatibility
    text = update.message.text.encode('utf-8').decode()
    # for debugging purposes only
    print("got text message :", text)
    # the first time you chat with the bot AKA the welcoming message
    if text == "/start":
        # print the welcoming message
        bot_welcome = """
                I am here to help you find your slot to get Vaccinated, I will also update you on the rising cases in your area!
                1. use /start to initialize me 
                2. use /news to get an update on current covid news on your area.
                3. use /bore and I will send you jokes to make you laugh.
                4. use /hospital to get contact number of your local hospitals and doctors available publicaly
                5. use /medical to  get contact pharmacies of your local area
                6. use /check for check availability of slots
                6. use /help for me to repeat all this for you
        """
        # send the welcoming message
        bot.sendMessage(chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id)

        
        # reply_markup = ReplyKeyboardMarkup([['good','bad'],['yes','no']],resize_keyboard=True,one_time_keyboard=True)

    elif text == "/check":
        bot_location = "HI! Give me Your location"
        keys = []
        keys.append([InlineKeyboardButton(text='Pincode',callback_data='pin'),InlineKeyboardButton(text='District',callback_data='dis')])
        reply_markup = InlineKeyboardMarkup(keys)
        bot.sendMessage(chat_id=chat_id, text=bot_location, reply_markup=reply_markup,reply_to_message_id=msg_id)
    elif text == "/news":
        keys = []
        keys.append([InlineKeyboardButton(text='State',callback_data='state'),InlineKeyboardButton(text='District',callback_data='dis')])
        reply_markup = InlineKeyboardMarkup(keys)
        bot.sendMessage(chat_id=chat_id, text=bot_location, reply_markup=reply_markup,reply_to_message_id=msg_id)
    else:
        try:
           # clear the message we got from any non alphabets
           text = re.sub(r"\W", "_", text)
           # create the api link for the avatar based on http://avatars.adorable.io/
           url = "https://api.adorable.io/avatars/285/{}.png".format(text.strip())
           # reply with a photo to the name the user sent,
           # note that you can send photos by url and telegram will fetch it for you
           bot.sendPhoto(chat_id=chat_id, photo=url, reply_to_message_id=msg_id)
        except Exception:
           # if things went wrong
           bot.sendMessage(chat_id=chat_id, text="There was a problem in the name you used, please enter different name", reply_to_message_id=msg_id)

   return 'ok'

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
   s = bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=TOKEN))
   if s:
       return "webhook setup ok"
   else:
       return "webhook setup failed"

@app.route('/')
def index():
   return '.'


if __name__ == '__main__':
   app.run(threaded=True)