import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import hashlib
from random import randint


def check_deezer_subscription_status(arl):
  API_URL = 'http://www.deezer.com/ajax/gw-light.php'
  SESSION_DATA = {
    'api_token': 'null',
    'api_version': '1.0',
    'input': '3',
    'method': 'deezer.getUserData'
  }
  USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
  session = requests.Session()
  session.headers.update({'User-Agent': USER_AGENT})

  try:
    res = session.post(API_URL, cookies={'arl': arl}, data=SESSION_DATA)
    res.raise_for_status()  # Raises an exception for non-successful response
  except requests.exceptions.RequestException:
    return "Connection failed"

  res = res.json()
  try:
    results = res['results']
    user_id = results['USER']['USER_ID']
    if user_id == 0:
      raise ValueError(
        'Could not login! Credentials wrong or nonexistent account!')
    country_co = results['COUNTRY']
    planD = results['OFFER_NAME']
    expireD = 'Unknown'
    ActiveD = True
    DLD = True
    LosslessD = results['USER']['OPTIONS']['web_sound_quality']['lossless']
    explictD = results['USER']['EXPLICIT_CONTENT_LEVEL']

    output = (f'ARL: `{arl}`\n'
              f'Country: {country_co} | ')

    if planD:
      output += (f'Plan: {planD} | Expiration: {expireD} | '
                 f'Active: {"🟢" if ActiveD else "🔴"} | '
                 f'Download: {"🟢" if DLD else "🔴"} | '
                 f'Lossless: {"🟢" if LosslessD else "🔴"} | '
                 f'Explicit: {"🟢" if explictD else "🔴"}')
    else:
      output += 'Active: "🔴"'

    return output

  except ValueError:
    return "Invalid Given ARL or nonexistent account!"


def get_qobuz_credentials():
  USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
  res = requests.get('https://play.qobuz.com/login',
                     headers={'User-Agent': USER_AGENT})
  soup = BeautifulSoup(res.text, 'html.parser')
  src_value = "https://play.qobuz.com" + soup.find(
    'script', src=lambda src: src and 'bundle.js' in src)['src']

  script_content = requests.get(src_value, headers={
    'User-Agent': USER_AGENT
  }).text
  pattern = r'production:{api:{appId:"(.*?)",appSecret:"(.*?)"}'
  matches = re.search(pattern, script_content)
  if matches:
    app_id, app_secret = matches.group(1), matches.group(2)
    return app_id, app_secret, src_value
  else:
    return "app id, app secret not found"


def get_account_details(email, password, app_id):
  # Define the URL with user input
  USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
  if "@" in email:
    url = f"https://www.qobuz.com/api.json/0.2/user/login?email={email}&password={password}&app_id={app_id}"
    response = requests.get(url, headers={'User-Agent': USER_AGENT})
    res = response.json()
    if 'status' not in res:
      user = res['user']
      userid = user['id']
      auth_token = res['user_auth_token']
      country_code = user['country_code']
      credential = user['credential']
      plan_label = credential['parameters']['label'] if credential[
        'parameters'] else None
      subscription_end_date = user['subscription']['end_date']
      active_subscription = datetime.now() < datetime.strptime(
        subscription_end_date, '%Y-%m-%d')
      store_features = user['store_features']
      streaming_enabled = store_features['streaming']
      download_enabled = store_features['download']
      hires_streaming_enabled = streaming_enabled and credential[
        'parameters'] and credential['parameters']['hires_streaming']
    else:
      return "Invalid Credentials"
  else:
    url = f"http://www.qobuz.com/api.json/0.2/user/get?user_id={email}&user_auth_token={password}&app_id={app_id}"

    response = requests.get(url, headers={'User-Agent': USER_AGENT})
    res = response.json()
    if 'status' not in res:
      userid = email
      auth_token = password
      country_code = res['country_code']
      credential = res['credential']
      plan_label = credential['parameters']['label'] if credential[
        'parameters'] else None
      subscription_end_date = res['subscription']['end_date']
      active_subscription = datetime.now() < datetime.strptime(
        subscription_end_date, '%Y-%m-%d')
      store_features = res['store_features']
      streaming_enabled = store_features['streaming']
      download_enabled = store_features['download']
      hires_streaming_enabled = streaming_enabled and credential[
        'parameters'] and credential['parameters']['hires_streaming']
    else:
      return "Invalid Credentials"

  # Prepare the account details
  output = (f'UserId: `{userid}`\n'
            f'Token: `{auth_token}`\n'
            f'Country: {country_code} | ')

  if plan_label:
    output += (f'Plan: {plan_label} | '
               f'Expiration: {subscription_end_date} | '
               f'Active: {"🟢" if active_subscription else "🔴"} | '
               f'Download: {"🟢" if download_enabled else "🔴"} | '
               f'Lossless: {"🟢" if hires_streaming_enabled else "🔴"} | '
               f'Explicit: {"🟢" if streaming_enabled else "🔴"}')
  else:
    output += 'Active: "🔴"'

  return output


def scrape_apple_music(url):
  con = url.split('/')[-4]
  albId = url.split('/')[-1].split('?')[0]
  itunes_endpoint = f"https://itunes.apple.com/lookup?id={albId}&country={con}&lang=en_us"
  print(itunes_endpoint)
  response = requests.get(itunes_endpoint)
  if response.status_code == 200:
    file_name = response.json()["results"][0]["collectionName"]
    artwork_link = response.json()["results"][0]["artworkUrl100"]
    artwork_link = artwork_link.replace("100x100bb.jpg", "3000x3000bb-999.jpg")
    print(artwork_link)
    endpoint = 'https://catbox.moe/user/api.php'
    data = {'reqtype': 'urlupload', 'url': artwork_link}
    response = requests.post(endpoint, data=data)
    print(response.url)
    return response.text, file_name


def fetch_animated_artwork(aurl):
  url = 'https://clients.dodoapps.io/playlist-precis/playlist-artwork.php'
  data = {'url': aurl, 'animation': True}
  response = requests.post(url, data=data)

  if response.status_code == 200:
    data = response.json()
    print(data)
    if data.get('animatedUrl'):
      # return data['animatedUrl']
      endpoint = 'https://catbox.moe/user/api.php'
      data = {'reqtype': 'urlupload', 'url': data['animatedUrl']}
      response = requests.post(endpoint, data=data)
      print(response.url)
      return response.text
    else:
      return 'No animated artwork for this album'
  else:
    return 'Failed to fetch artwork'


def genarl(session, payload={}):
  params = {
    'method': 'user.getArl',
    'input': 3,
    'api_version': 1.0,
    'api_token': '',
    'cid': randint(0, 1e9),
  }
  return session.post('https://www.deezer.com/ajax/gw-light.php',
                      params=params,
                      json=payload).json()


def arl_via_email(email, password):
  password = hashlib.md5(password.encode()).hexdigest()
  client_id, client_secret = "447462", "a83bf7f38ad2f137e444727cfc3775cf"
  params = {
    'app_id': client_id,
    'login': email,
    'password': password,
    'hash':
    hashlib.md5(
      (client_id + email + password + client_secret).encode()).hexdigest(),
  }
  session = requests.Session()
  json = session.get('https://connect.deezer.com/oauth/user_auth.php',
                     params=params).json()
  if 'error' in json:
    return "Invalid credentials"
  else:
    headers = {'Authorization': f'Bearer {json["access_token"]}'}
    session.get('https://api.deezer.com/platform/generic/track/80085',
                headers=headers)
    return genarl(session)["results"]


def send_log_message(message):
  bot.send_message(chat_id=log_channel_id, text=message)
