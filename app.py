'''
vaccine bot to help people get vaccinated.
'''


### Imports ############
import re
import configparser
from flask import Flask, request
import telegram
from telegram import ReplyKeyboardMarkup, KeyboardButton,InlineKeyboardMarkup,InlineKeyboardButton
import requests
from country import Country
import telegramcalendar

parser = configparser.ConfigParser()
parser.read('credentials/config.conf')




global bot
global TOKEN
global news_state_api
global news_district_api
global Track_user

### config #########
TOKEN = parser['Telebot']['token']
URL = parser['Telebot']['URL']
news_state_api = parser['Extapi']['news_state']
news_district_api = parser['Extapi']['news_district']


## bot init ##########
bot = telegram.Bot(token=TOKEN)


country = Country()
states = country.get_states()

covid_data_state_dict = {}
covid_data_district_dict = {}

Track_user = {}

app = Flask(__name__)


District = []


def set_track_user(id,text):
    global Track_user
    Track_user[id] = text

@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    callback_query = update.callback_query


    #print(update)
    if callback_query is not None:
        if callback_query.data == "state_slot":
            bot_text = "Enter the State name:"
            reply_markup = ReplyKeyboardMarkup(states,resize_keyboard=True,one_time_keyboard=True)
            bot.sendMessage(chat_id=callback_query.message.chat.id,text=bot_text, reply_markup=reply_markup, reply_to_message_id=callback_query.message.message_id)
            return 'ok'

        elif callback_query.data == "dis_slot":
            bot_text = "Enter the State name:"
            reply_markup = ReplyKeyboardMarkup(states,resize_keyboard=True,one_time_keyboard=True)
            bot.sendMessage(chat_id=callback_query.message.chat.id,text=bot_text, reply_markup=reply_markup, reply_to_message_id=callback_query.message.message_id)
            
            if Track_user[callback_query.message.chat.id] == 'NEWS':
                set_track_user(callback_query.message.chat.id,'NEWS_dis')
            elif Track_user[callback_query.message.chat.id] == 'CHECK':
                set_track_user(callback_query.message.chat.id,'CHECK_dis')
            return 'ok'
            
        elif callback_query.data == "pin_slot":
            bot_text = "Enter the Pincode name:"
            set_track_user(callback_query.message.chat.id,'CHECK_pin')
            return 'ok'

    if update.message is None:
        return 'BAD Request'


    
    chat_id = update.message.chat.id
    msg_id = update.message.message_id

    # Telegram understands UTF-8, so encode text for unicode compatibility
    text = update.message.text.encode('utf-8').decode()

    # for debugging purposes only
    print("got text message :", text)

    # the welcoming message ####################3
    if text == "/start":
        # print the welcoming message ######################
        bot_welcome = """
                I am here to help you find your slot to get Vaccinated, I will also update you on the rising cases in your area!
                1. use /start to initialize me 
                2. use /news to get an update on current covid news on your area.
                3. use /bore and I will send you jokes to make you laugh.
                4. use /hospital to get contact number of your local hospitals and doctors available publicaly
                5. use /medical to  get contact pharmacies of your local area
                6. use /check_availability for check availability of slots
                6. use /help for me to repeat all this for you
        """
        # send the welcoming message
        bot.sendMessage(chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id)

        ### /check availability #########################
    elif text == "/check_availability":
        bot_check_avail = "HI! Give me Your location"
        keys_inline = []
        kekeys_inlineys.append([InlineKeyboardButton(text='Pincode',callback_data='pin_slot'),InlineKeyboardButton(text='District',callback_data='dis_slot')])
        reply_markup = InlineKeyboardMarkup(keys_inline)
        bot.sendMessage(chat_id=chat_id, text=bot_check_avail, reply_markup=reply_markup,reply_to_message_id=msg_id)

        ########### track user ##########
        set_track_user(chat_id,'CHECK')


        ##### news ###############
    elif text == "/news":
        bot_news = "For which region you want data?"
        keys_inline = []
        keys_inline.append([InlineKeyboardButton(text='State',callback_data='state_slot'),InlineKeyboardButton(text='District',callback_data='dis_slot')])
        reply_markup = InlineKeyboardMarkup(keys_inline)
        bot.sendMessage(chat_id=chat_id, text=bot_news, reply_markup=reply_markup,reply_to_message_id=msg_id)

        ################## after sending ###########
        global covid_data_state_dict
        global covid_data_district_dict

        ########### get covid news state wise ##################
        covid_data_state = requests.get(news_state_api)
        covid_data_state = covid_data_state.json()
        covid_data_state_dict = {}
        for i in covid_data_state:
            if i['state_name'] == '':
                i['state_name'] = 'Unknown'
            covid_data_state_dict[i['state_name']] = i

        ########### user track id #############
        set_track_user(chat_id,'NEWS')

        ########### get covid news district wise ##################
        covid_data_district_dict = {}
        covid_data_district = requests.get(news_district_api)
        covid_data_district = covid_data_district.json()
        for s in country.get_flat_states():
            if s in covid_data_district:
                covid_data_district_dict.update(covid_data_district[s]['districtData'])



    else:

        ##### for debuging ############
        print(Track_user)

        try:
            print(Track_user[chat_id])
            if Track_user[chat_id] == 'NEWS_dis':
                if text in country.get_flat_states():
                    bot_text = "Enter the district:"
                    districts = country.get_district(text)
                    reply_markup = ReplyKeyboardMarkup(districts,resize_keyboard=True,one_time_keyboard=True)
                    bot.sendMessage(chat_id=chat_id,text=bot_text, reply_markup=reply_markup, reply_to_message_id=msg_id)
                    set_track_user(chat_id,'NEWS')
            elif Track_user[chat_id] == 'CHECK_dis':
                if text in country.get_flat_states():
                    bot_text = "Enter the district:"
                    districts = country.get_district(text)
                    reply_markup = ReplyKeyboardMarkup(districts,resize_keyboard=True,one_time_keyboard=True)
                    bot.sendMessage(chat_id=chat_id,text=bot_text, reply_markup=reply_markup, reply_to_message_id=msg_id)
                    set_track_user(chat_id,'CHECK_date')
            elif Track_user[chat_id] == 'NEWS':
                covid_req = {}
                if text in country.get_flat_states():
                    covid_req = covid_data_state_dict[text]
                    covid_text = 'Hey! There are {} no. of active cases and {} recovered from coronavirus in {} state. And only {} no. of deaths held due to covid. So, Don\'t worry. \nTotal confirmed cases are {}'.format(covid_req['new_active'],covid_req['new_cured'],covid_req['state_name'],covid_req['new_death'],covid_req['new_positive'])
                    bot.sendMessage(chat_id=chat_id, text=covid_text, reply_to_message_id=msg_id)   
                elif text in covid_data_district_dict:
                    covid_req = covid_data_district_dict[text]
                    covid_text = 'Hey! There are {} no. of active cases and {} recovered from coronavirus in {} District. And only {} no. of deaths held due to covid. So, Don\'t worry. \nTotal confirmed cases are {}'.format(covid_req['active'],covid_req['recovered'],text,covid_req['deceased'],covid_req['confirmed'])
                    bot.sendMessage(chat_id=chat_id, text=covid_text, reply_to_message_id=msg_id)
            elif Track_user[chat_id] == 'CHECK_date':
                print(text)
                bot_text = 'Enter  the date:'
                reply_markup = telegramcalendar.create_calendar()
                bot.sendMessage(chat_id=chat_id, text=bot_text, reply_markup=reply_markup, reply_to_message_id=msg_id)
                pass
            


            # clear the message we got from any non alphabets
            text = re.sub(r"\W", "_", text)
            # create the api link for the avatar based on http://avatars.adorable.io/
            url = "https://api.adorable.io/avatars/285/{}.png".format('good')
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
   print('working')