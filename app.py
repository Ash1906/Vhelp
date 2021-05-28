'''
vaccine bot to help people get vaccinated.
'''

import re
import configparser
from flask import Flask, request
import telegram
from telegram import ReplyKeyboardMarkup, KeyboardButton,InlineKeyboardMarkup,InlineKeyboardButton
import requests
from country import Country

parser = configparser.ConfigParser()
parser.read('credentials/config.conf')




global bot
global TOKEN
TOKEN = parser['Telebot']['token']
URL = parser['Telebot']['URL']
bot = telegram.Bot(token=TOKEN)

country = Country()
states = country.get_states()

covid_data_state_dict = {}
covid_data_district_dict = {}

app = Flask(__name__)


news_api_district = 'https://api.covid19india.org/state_district_wise.json'
news_api_state = 'https://www.mohfw.gov.in/data/datanew.json'


District = []


@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    callback_query = update.callback_query
    print(update)
    if callback_query is not None:
        if callback_query.data == "state":
            bot_state = "Enter the state name:"
            reply_markup = ReplyKeyboardMarkup(states,resize_keyboard=True,one_time_keyboard=True)
            bot.sendMessage(chat_id=callback_query.message.chat.id,text=bot_state, reply_markup=reply_markup, reply_to_message_id=callback_query.message.message_id)
            return 'ok'
        elif callback_query.data == "dis":
            bot_district = "Enter the State for which it belongs:"
            reply_markup = []
            for i in states:
                disctric_key = []
                for j in i:
                    disctric_key.append(InlineKeyboardButton(text=j,callback_data=j))
                reply_markup.append(disctric_key)
            reply_markup = InlineKeyboardMarkup(reply_markup)
            bot.sendMessage(chat_id=callback_query.message.chat.id, text=bot_district, reply_markup=reply_markup,reply_to_message_id=callback_query.message.message_id)
        else:
            if callback_query.data in country.get_flat_states():
                bot_district = "Enter the district:"
                districts = country.get_district(callback_query.data)
                reply_markup = ReplyKeyboardMarkup(districts,resize_keyboard=True,one_time_keyboard=True)
                bot.sendMessage(chat_id=callback_query.message.chat.id,text=bot_district, reply_markup=reply_markup, reply_to_message_id=callback_query.message.message_id)


    if update.message is None:
        return 'BAD request'
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
     elif text == "/bore":
         re = requests.get("https://official-joke-api.appspot.com/random_joke")
#print(re.status_code)
#print(re.text)
         dict = re.json()
         punch = dict['setup'] +" " +  dict['punchline']

        # print the welcoming message
        # send the welcoming message
        bot.sendMessage(chat_id=chat_id, text=punch, reply_to_message_id=msg_id)

        
        # reply_markup = ReplyKeyboardMarkup([['good','bad'],['yes','no']],resize_keyboard=True,one_time_keyboard=True)

    elif text == "/check":
        bot_location = "HI! Give me Your location"
        keys = []
        keys.append([InlineKeyboardButton(text='Pincode',callback_data='pin'),InlineKeyboardButton(text='District',callback_data='dis')])
        reply_markup = InlineKeyboardMarkup(keys)
        bot.sendMessage(chat_id=chat_id, text=bot_location, reply_markup=reply_markup,reply_to_message_id=msg_id)
    
    elif text == "/news":
        bot_location = "For which region you want data?"
        keys = []
        keys.append([InlineKeyboardButton(text='State',callback_data='state'),InlineKeyboardButton(text='District',callback_data='dis')])
        reply_markup = InlineKeyboardMarkup(keys)
        bot.sendMessage(chat_id=chat_id, text=bot_location, reply_markup=reply_markup,reply_to_message_id=msg_id)
        global covid_data_state_dict
        global covid_data_district_dict
        covid_data_state = requests.get(news_api_state)
        covid_data_state = covid_data_state.json()
        covid_data_state_dict = {}
        for i in covid_data_state:
            if i['state_name'] == '':
                i['state_name'] = 'Unknown'
            covid_data_state_dict[i['state_name']] = i
        
        covid_data_district_dict = {}
        covid_data_district = requests.get(news_api_district)
        covid_data_district = covid_data_district.json()
        for s in country.get_flat_states():
            if s in covid_data_district:
                covid_data_district_dict.update(covid_data_district[s]['districtData'])



    else:
        try:
            covid_req = {}
            print(text)
            print(country.get_flat_states())
            print(covid_data_district_dict.keys())
            if text in country.get_flat_states():
                covid_req = covid_data_state_dict[text]
                print(covid_req)
                covid_text = 'Hey! There are {} no. of active cases and {} recovered from coronavirus in {} state. And only {} no. of deaths held due to covid. So, Don\'t worry. \nTotal confirmed cases are {}'.format(covid_req['new_active'],covid_req['new_cured'],covid_req['state_name'],covid_req['new_death'],covid_req['new_positive'])
                bot.sendMessage(chat_id=chat_id, text=covid_text, reply_to_message_id=msg_id)
            elif text in covid_data_district_dict:
                covid_req = covid_data_district_dict[text]
                print(covid_req)
                covid_text = 'Hey! There are {} no. of active cases and {} recovered from coronavirus in {} District. And only {} no. of deaths held due to covid. So, Don\'t worry. \nTotal confirmed cases are {}'.format(covid_req['active'],covid_req['recovered'],text,covid_req['deceased'],covid_req['confirmed'])
                bot.sendMessage(chat_id=chat_id, text=covid_text, reply_to_message_id=msg_id)
            


            # clear the message we got from any non alphabets
            text = re.sub(r"\W", "_", text)
            # create the api link for the avatar based on http://avatars.adorable.io/
            url = "https://api.adorable.io/avatars/285/{}.png".format('good')
            # reply with a photo to the name the user sent,
            # note that you can send photos by url and telegram will fetch it for you
            #bot.sendPhoto(chat_id=chat_id, photo=url, reply_to_message_id=msg_id)
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