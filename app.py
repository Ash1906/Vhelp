'''
vaccine bot to help people get vaccinated.
'''


### Imports ############
import re
import configparser
from flask import Flask, request
import telegram
from telegram import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton, 
    ReplyKeyboardRemove, 
    ChatAction 
    )
import requests
from requests.models import PreparedRequest
from country import Country
import telegramcalender
import pickle
import time
import sqlalchemy
from apscheduler.schedulers.background import BackgroundScheduler


scheduler = BackgroundScheduler({'apscheduler.timezone': 'Asia/Calcutta'})

# scheduler.add_jobstore('sqlalchemy', url='sqlite:////tmp/schedule.db')





@scheduler.scheduled_job('interval', minutes=3)
def timed_job():
    print('This job is run every three minutes.')

@scheduler.scheduled_job('cron', day_of_week='mon-fri', hour=6)
def scheduled_job():
    print('This job is run every weekday at 5pm.')


scheduler.start()

parser = configparser.ConfigParser()
parser.read('credentials/config.conf')




global bot
global TOKEN
global news_state_api
global news_district_api


### config #########
TOKEN = parser['Telebot']['token']
URL = parser['Telebot']['URL']
BORE = parser['Extapi']['bore']
news_state_api = parser['Extapi']['news_state']
news_district_api = parser['Extapi']['news_district']
slotbyD = parser['Extapi']['slotbyD']
slotbyP = parser['Extapi']['slotbyP']
quote = parser['Extapi']['quote']

## bot init ##########
bot = telegram.Bot(token=TOKEN)


country = Country()

states = country.get_states()
check_states = country.get_check_states()

covid_data_state_dict = {}
covid_data_district_dict = {}
pr_quo_list = []


app = Flask(__name__)


def update_user(chat_id,param,data):
    try:
        User = []
        with open('user_stat.txt','rb') as f:
            User = pickle.load(f)
            if chat_id not in User:
                User[chat_id] = {}
                User[chat_id][param] = data
            else:
                User[chat_id][param] = data
        with open('user_stat.txt','wb') as f:
            pickle.dump(User,f,protocol=pickle.HIGHEST_PROTOCOL)
    except EOFError:
        print('ERROR')


def read_user(chat_id,param):
    try:
        with open('user_stat.txt','rb') as f:
            User = pickle.load(f)
            if chat_id in User:
                if param in User[chat_id]:
                    return User[chat_id][param]
            
        return False
    except EOFError:
        print('ERROR')

def remove_user(chat_id):
    try:
        User = []
        with open('user_stat.txt','rb') as f:
            User = pickle.load(f)
            if chat_id  in User:
                del User[chat_id]
        with open('user_stat.txt','wb') as f:
            pickle.dump(User,f,protocol=pickle.HIGHEST_PROTOCOL)
    except EOFError:
        print('ERROR')


# def get_object():
#     with open('stat.txt','rb') as f:
#         status = pickle.load(f)
#         return status

def send_slot_data(bot,param1,param2,filter,chat_id,msg_id,url):
    params = {filter:param1,'date':param2}
    req = PreparedRequest()
    req.prepare_url(url, params)
    headers = {'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"}
    data = requests.get(req.url,headers=headers)
    print(req.url)
    data = data.json()
    # print(data)
    count = 0
    text = 'No sessions found for this date!'
    if 'centers' in data:
        print('good')
        if len(data['centers'])>0:
            
            for i in data['centers']:
                try:
                    # print(i)
                    if next(item for item in i['sessions'] if item["available_capacity"]>0):
                        print('working')
                        text = 'Here are the slots we find for you!\nFor state {} in district {} :\nCenter name : {}\nAddress : {}\nFee Type : {}\n'.format(i['state_name'],i['district_name'],i['name'],i['address'],i['fee_type'])
                        bot.sendMessage(chat_id=chat_id, text=text)
                        for j in i['sessions']:
                            text2 = 'Sessions:\ndate: {}\nAge limit: {}\nvaccine: {}\ndose 1: {}\ndose availablity \ndose 2: {}\nslots: {}\n'.format(j['date'],j['min_age_limit'],j['vaccine'],j['available_capacity_dose1'],j['available_capacity_dose2'],'\nslots: '.join(j['slots']))
                            bot.sendMessage(chat_id=chat_id, text=text2)
                            count+=1
                except StopIteration:
                    print('No sessions found at center {}'.format(i['name']))

    return count

District = []

@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    try:
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        callback_query = update.callback_query

        if callback_query is not None:
            if callback_query.data == "state_slot":
                bot_text = "Enter the State name:"
                reply_markup = ReplyKeyboardMarkup(states,resize_keyboard=True,one_time_keyboard=True)
                bot.sendMessage(chat_id=callback_query.message.chat.id,text=bot_text, reply_markup=reply_markup, reply_to_message_id=callback_query.message.message_id)
                return 'ok'

            elif callback_query.data == "dis_slot":
                bot_text = "Enter the State name:"
                reply_markup = ReplyKeyboardMarkup(check_states,resize_keyboard=True,one_time_keyboard=True)
                bot.sendMessage(chat_id=callback_query.message.chat.id,text=bot_text, reply_markup=reply_markup, reply_to_message_id=callback_query.message.message_id)
                if read_user(callback_query.message.chat.id,'status') == 'NEWS':
                    update_user(callback_query.message.chat.id,'status','NEWS_dis')
                elif read_user(callback_query.message.chat.id,'status') == 'CHECK':
                    update_user(callback_query.message.chat.id,'status','CHECK_dis')
                elif read_user(callback_query.message.chat.id,'status') == 'SUBSCRIBE':
                    update_user(callback_query.message.chat.id,'status','SUBSCRIBE_dis')
                return 'ok'
                
            elif callback_query.data == "pin_slot":
                bot_text = "Enter the Pincode name:"
                bot.sendMessage(chat_id=callback_query.message.chat.id, text=bot_text)
                if read_user(callback_query.message.chat.id,'status') == 'CHECK':
                    update_user(callback_query.message.chat.id,'status','CHECK_pin')
                elif read_user(callback_query.message.chat.id,'status') == 'SUBSCRIBE':
                    update_user(callback_query.message.chat.id,'status','SUBSCRIBE_add_pin')
                return 'ok'
            elif 'CHECK,' in read_user(callback_query.message.chat.id,'status') or 'CHECKPIN,' in read_user_stat(callback_query.message.chat.id):
                try: 
                    call_back,_,_,_ = telegramcalender.separate_callback_data(callback_query.data)
                except Exception:
                    print('Error')
                if call_back in ['IGNORE', 'DAY','PREV-MONTH','NEXT-MONTH']:
                    # print('all good')
                    selected,date = telegramcalender.process_calendar_selection(bot, update)
                    if selected:
                        bot.send_message(chat_id=callback_query.message.chat.id,
                                        text="You selected %s" % (date.strftime("%d-%m-%Y")),
                                        reply_markup=ReplyKeyboardRemove())
                        bot.send_chat_action(chat_id=callback_query.message.chat.id, action=ChatAction.TYPING)
                        if 'CHECK,' in read_user(callback_query.message.chat.id,'status'):
                            _,district = read_user(callback_query.message.chat.id,'status').split(',')
                            id = country.get_district_id(district)
                            print(id,date.strftime("%d-%m-%Y"))
                            ret = send_slot_data(bot,id,date.strftime("%d-%m-%Y"),'district_id',callback_query.message.chat.id,callback_query.message.message_id,slotbyD)
                            if ret == 0:
                                bot.sendMessage(chat_id=callback_query.message.chat.id, text='No sessions found for this date!')

                        elif 'CHECKPIN,' in read_user(callback_query.message.chat.id,'status'):
                            _,pincode = read_user(callback_query.message.chat.id,'status').split(',')
                            ret = send_slot_data(bot,pincode,date.strftime("%d-%m-%Y"),'pincode',callback_query.message.chat.id,callback_query.message.message_id,slotbyP)
                            if ret == 0:
                                bot.sendMessage(chat_id=callback_query.message.chat.id, text='No sessions found for this date!')
                        update_user(callback_query.message.chat.id,'status','DONE')
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
                    2. use /news to get an update on current covid news on your area
                    3. use /bore and I will send you jokes to make you laugh
                    4. use /check_availability for check availability of slots
                    5. use /add_subcription for get slot alert
                    6. use /my_subcriptions to view your subcriptions
                    7. use /remove_subcription to remove subcription
                    8. use /help to know how I work
                    9. use /share to share me with family and friends
                    10. use /delete_all Delete my data stored

                    Thank you for choosing me. I am glad to help you and others. Share with other people too.
            """
            # send the welcoming message
            bot.sendMessage(chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id)
        elif text == "/help":
            bot_welcome = """  
            I am a telegram bot who can helpyou find your vaccination slots.
            I am designed to save your time and efforts you spend on Co-Win. 
            Vaccination is one way to protect yourself and your family from this deadly virus.
            I encourage you to get vaccinated as soon as possible 
            Use me and share with others too.

            Here is the list of commands you can use :

                    1. use /start to initialize me 
                    2. use /news to get an update on current covid news on your area
                    3. use /bore and I will send you jokes to make you laugh
                    4. use /check_availability for check availability of slots
                    5. use /help to know how I work
                    6. use /share to share me with family and friends

                    Thank you for choosing me. I am glad to help you and others. Share with other people too.
            """
            # send the welcoming message
            bot.sendMessage(chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id)

        ########### bore #################
        elif text == "/bore":
            re = requests.get(BORE)
            joke = re.json()
            punch = joke['setup'] +" " +  joke['punchline']
            bot.sendMessage(chat_id=chat_id, text=punch, reply_to_message_id=msg_id)

            ### /check availability #########################
        elif text == "/check_availability":
            bot_check_avail = "HI! Give me Your location"
            keys_inline = []
            keys_inline.append([InlineKeyboardButton(text='Pincode',callback_data='pin_slot'),InlineKeyboardButton(text='District',callback_data='dis_slot')])
            reply_markup = InlineKeyboardMarkup(keys_inline)
            bot.sendMessage(chat_id=chat_id, text=bot_check_avail, reply_markup=reply_markup,reply_to_message_id=msg_id)

            ########### track user ##########
            update_user(chat_id,'status','CHECK')


            ##### news ###############
        elif text == "/delete_all":
            pass
        elif text == "/remove_subcription":
            subscrib  = read_user(chat_id,'Subcriptions')
            if subscrib:
                bot_text = 'Select the region you want to remove:'
                key_buttons = subscrib['dis'] + subscrib['pin']
                reply_markup = ReplyKeyboardMarkup([key_buttons],resize_keyboard=True,one_time_keyboard=True)
                bot.sendMessage(chat_id=chat_id,text=bot_text, reply_markup=reply_markup, reply_to_message_id=msg_id)
                update_user(chat_id,'status','SUBSCRIBE_rem')
            else:
                bot_text = 'You have no subcriptions!'
                bot.sendMessage(chat_id=chat_id, text=bot_text, reply_to_message_id=msg_id)


        elif text == "/my_subcriptions":
            subscrib  = read_user(chat_id,'Subcriptions')
            bot_text = ''
            if subscrib:
                print(subscrib)
                bot_text = 'Here are Your Subcriptions:\n'
                bot_text += '{}\n{}'.format('\n'.join(subscrib['dis']),'\n'.join(subscrib['pin']))
            else:
                bot_text = 'You have no subcriptions!'
            bot.sendMessage(chat_id=chat_id, text=bot_text, reply_to_message_id=msg_id)

        elif text == "/add_subcription":
            bot_subscribe = "HI! Let's Subscribe Your region:" 

            keys_inline = []
            keys_inline.append([InlineKeyboardButton(text='Pincode',callback_data='pin_slot'),InlineKeyboardButton(text='District',callback_data='dis_slot')])
            reply_markup = InlineKeyboardMarkup(keys_inline)
            bot.sendMessage(chat_id=chat_id, text=bot_subscribe, reply_markup=reply_markup,reply_to_message_id=msg_id)

            update_user(chat_id,'status','SUBSCRIBE')

        elif text == "/news":
            bot_news = "For which region you want data?"
            keys_inline = []
            keys_inline.append([InlineKeyboardButton(text='State',callback_data='state_slot'),InlineKeyboardButton(text='District',callback_data='dis_slot')])
            reply_markup = InlineKeyboardMarkup(keys_inline)
            bot.sendMessage(chat_id=chat_id, text=bot_news, reply_markup=reply_markup,reply_to_message_id=msg_id)


            ################## after sending ###########
            global covid_data_state_dict
            global covid_data_district_dict
            global pr_quo_list

            ########### get covid news state wise ##################
            covid_data_state = requests.get(news_state_api)
            covid_data_state = covid_data_state.json()
            covid_data_state_dict = {}
            for i in covid_data_state:
                if i['state_name'] == '':
                    i['state_name'] = 'Unknown'
                covid_data_state_dict[i['state_name']] = i

            #########Get quote ###################
            req = requests.get(quote)
            quo = req.json()
            pr_quo_list = [i['q'] for i in quo if 'q' in i]
            

            ########### user track id #############
            update_user(chat_id,'status','NEWS')
            ########### get covid news district wise ##################
            covid_data_district_dict = {}
            covid_data_district = requests.get(news_district_api)
            covid_data_district = covid_data_district.json()
            for s in country.get_flat_states():
                if s in covid_data_district:
                    covid_data_district_dict.update(covid_data_district[s]['districtData'])



        else:

            ##### for debuging ############
            # if read_user_stat(chat_id) == 'CHECK_date':
            #     print(text)
            #     bot_text = 'Enter  the date:'
            #     reply_markup = telegramcalender.create_calendar()
            #     bot.sendMessage(chat_id=chat_id, text=bot_text, reply_markup=reply_markup, reply_to_message_id=msg_id)
            print(read_user(chat_id,'status'))
            if read_user(chat_id,'status') == 'NEWS_dis':
                if text in country.get_flat_states():
                    bot_text = "Enter the district:"
                    districts = country.get_district(text)
                    reply_markup = ReplyKeyboardMarkup(districts,resize_keyboard=True,one_time_keyboard=True)
                    bot.sendMessage(chat_id=chat_id,text=bot_text, reply_markup=reply_markup, reply_to_message_id=msg_id)
                    update_user(chat_id,'status','NEWS')
            elif read_user(chat_id,'status') == 'CHECK_dis':
                if text in country.get_flat_check_states():
                    bot_text = "Enter the district:"
                    districts = country.get_check_district(text)
                    reply_markup = ReplyKeyboardMarkup(districts,resize_keyboard=True,one_time_keyboard=True)
                    bot.sendMessage(chat_id=chat_id,text=bot_text, reply_markup=reply_markup, reply_to_message_id=msg_id)
                    update_user(chat_id,'status','CHECK_date')
            elif read_user(chat_id,'status') == 'SUBSCRIBE_dis':
                if text in country.get_flat_check_states():
                    bot_text = "Enter the district:"
                    districts = country.get_check_district(text)
                    reply_markup = ReplyKeyboardMarkup(districts,resize_keyboard=True,one_time_keyboard=True)
                    bot.sendMessage(chat_id=chat_id,text=bot_text, reply_markup=reply_markup, reply_to_message_id=msg_id)
                    update_user(chat_id,'status','SUBSCRIBE_add_dis')
            elif read_user(chat_id,'status') == 'NEWS':
                covid_req = {}
                if text in country.get_flat_states():
                    covid_req = covid_data_state_dict[text]
                    covid_text = 'Hey! There are {} no. of active cases and {} recovered from coronavirus in {} state. And only {} no. of deaths held due to covid. So, Don\'t worry. \nTotal confirmed cases are {}'.format(covid_req['new_active'],covid_req['new_cured'],covid_req['state_name'],covid_req['new_death'],covid_req['new_positive'])
                    pr_quo= pr_quo_list[0]
                    bot.sendMessage(chat_id=chat_id, text=covid_text, reply_to_message_id=msg_id)   
                    bot.sendMessage(chat_id=chat_id, text=pr_quo)
                    
                elif text in covid_data_district_dict:
                    covid_req = covid_data_district_dict[text]
                    covid_text = 'Hey! There are {} no. of active cases and {} recovered from coronavirus in {} District. And only {} no. of deaths held due to covid. So, Don\'t worry. \nTotal confirmed cases are {}'.format(covid_req['active'],covid_req['recovered'],text,covid_req['deceased'],covid_req['confirmed'])
                    pr_quo= pr_quo_list[0]
                    bot.sendMessage(chat_id=chat_id, text=covid_text, reply_to_message_id=msg_id)
                    bot.sendMessage(chat_id=chat_id, text=pr_quo)
                update_user(chat_id,'status','DONE')
            elif read_user(chat_id,'status') == 'CHECK_date':
                bot_text = 'Enter  the date:'
                reply_markup = telegramcalender.create_calendar()
                update.message.reply_text("Please select a date: ", reply_markup=telegramcalender.create_calendar())
                update_user(chat_id,'status','CHECK,'+text)
            elif read_user(chat_id,'status') == 'CHECK_pin':
                bot_text = 'Enter  the pincode:'
                reply_markup = telegramcalender.create_calendar()
                update.message.reply_text("Please select a date: ", reply_markup=telegramcalender.create_calendar())
                update_user(chat_id,'status','CHECKPIN,'+text)
            elif read_user(chat_id,'status') == 'SUBSCRIBE_add_dis':
                subscrib  = read_user(chat_id,'Subcriptions')
                if subscrib:
                    if text not in subscrib['dis']:
                        subscrib['dis'].append(text)
                else:
                    subscrib = {'dis':[],'pin':[]}
                    subscrib['dis'].append(text)
                update_user(chat_id,'Subcriptions',subscrib)
                update_user(chat_id,'status','DONE')
            elif read_user(chat_id,'status') == 'SUBSCRIBE_add_pin':
                subscrib  = read_user(chat_id,'Subcriptions')
                if subscrib:
                    if text not in subscrib['pin']:
                        subscrib['pin'].append(text)
                else:
                    subscrib = {'dis':[],'pin':[]}
                    subscrib['pin'].append(text)
                update_user(chat_id,'Subcriptions',subscrib)
                update_user(chat_id,'status','DONE')
            elif read_user(chat_id,'status') ==  'SUBSCRIBE_rem':
                subscrib  = read_user(chat_id,'Subcriptions')
                if subscrib:
                    if text in subscrib['pin']:
                        subscrib['pin'].remove(text)
                    elif text in subscrib['dis']:
                        subscrib['dis'].remove(text)
                update_user(chat_id,'Subcriptions',subscrib)
                update_user(chat_id,'status','DONE')







    except Exception as e:
        # if things went wrong
        print('error',e)
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
