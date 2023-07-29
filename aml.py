import datetime
import re
import shutil
from http.cookiejar import MozillaCookieJar
from pathlib import Path
from xml.etree import ElementTree
import requests


def get_session(cookies_location):
    cookies = MozillaCookieJar(cookies_location)
    cookies.load(ignore_discard=True, ignore_expires=True)
    session = requests.Session()
    session.cookies.update(cookies)
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "content-type": "application/json",
            "Media-User-Token": session.cookies.get_dict()["media-user-token"],
            "x-apple-renewal": "true",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "origin": "https://beta.music.apple.com",
        }
    )
    web_page = session.get("https://beta.music.apple.com").text
    index_js_uri = re.search(r"/assets/index-legacy-[^/]+\.js", web_page).group(0)
    index_js_page = session.get(f"https://beta.music.apple.com{index_js_uri}").text
    token = re.search('(?=eyJh)(.*?)(?=")', index_js_page).group(1)
    session.headers.update({"authorization": f"Bearer {token}"})
    return session


def get_lyrics(session, country, track_id):
    try:
        lyrics_ttml = ElementTree.fromstring(
            session.get(
                f"https://amp-api.music.apple.com/v1/catalog/{country}/songs/{track_id}/lyrics"
            ).json()["data"][0]["attributes"]["ttml"]
        )
    except:
        return None, None
    unsynced_lyrics = ""
    synced_lyrics = ""
    for div in lyrics_ttml.iter("{http://www.w3.org/ns/ttml}div"):
        for p in div.iter("{http://www.w3.org/ns/ttml}p"):
            if p.attrib.get("begin"):
                synced_lyrics += f'[{get_synced_lyrics_formatted_time(p.attrib.get("begin"))}]{p.text}\n'
            if p.text is not None:
                unsynced_lyrics += p.text + "\n"
        unsynced_lyrics += "\n"
    return unsynced_lyrics[:-2], synced_lyrics


def get_synced_lyrics_formatted_time(unformatted_time):
    unformatted_time = (
        unformatted_time.replace("m", "").replace("s", "").replace(":", ".")
    )
    unformatted_time = unformatted_time.split(".")
    m, s, ms = 0, 0, 0
    ms = int(unformatted_time[-1])
    if len(unformatted_time) >= 2:
        s = int(unformatted_time[-2]) * 1000
    if len(unformatted_time) >= 3:
        m = int(unformatted_time[-3]) * 60000
    unformatted_time = datetime.datetime.fromtimestamp((ms + s + m) / 1000.0)
    ms_new = f"{int(str(unformatted_time.microsecond)[:3]):03d}"
    if int(ms_new[2]) >= 5:
        ms = int(f"{int(ms_new[:2]) + 1}") * 10
        unformatted_time += datetime.timedelta(
            milliseconds=ms
        ) - datetime.timedelta(microseconds=unformatted_time.microsecond)
    return unformatted_time.strftime("%M:%S.%f")[:-4]


def make_lrc(final_location, synced_lyrics):
    if synced_lyrics:
        with open(final_location.with_suffix(".lrc"), "w", encoding="utf8") as f:
            f.write(synced_lyrics)


def main(cookies_location, track_id, final_path):
    session = get_session(cookies_location)
    country = session.cookies.get_dict()["itua"]
    unsynced_lyrics, synced_lyrics = get_lyrics(session, country, track_id)
    if synced_lyrics or unsynced_lyrics :
      Path(final_path).mkdir(parents=True, exist_ok=True)
      it = f"https://itunes.apple.com/lookup?id={track_id}&country={country}&lang=en_us"
      Names = requests.get(it).json()
      track_num, track_name = Names["results"][0]["trackNumber"], Names["results"][0]["trackName"]
    # Write the synced lyrics directly to the final path
      final_location = Path(final_path) / f"{track_num}.{track_name}.txt"
      make_lrc(final_location, synced_lyrics)
    else :
      print("lyrics for the track")
