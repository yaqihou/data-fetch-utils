
import os
import time
from tqdm import tqdm
import datetime as dt
import parsedatetime as pdt

import requests

from PIL import Image, ImageDraw, ImageFont

def wait_with_count(sleep_time, desc="Waiting for"):

    for _ in (bar := tqdm(range(sleep_time),
                            desc=desc,
                            miniters=1,
                            # ncols=0,
                            # dynamic_ncols=False,
                            bar_format='{desc}: {elapsed}<{remaining}'
                            )):
        time.sleep(1)

def next_weekday(date, weekday) -> dt.date:
    days_ahead = weekday - date.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    ret = date + dt.timedelta(days_ahead)
    assert isinstance(ret, dt.date)
    return ret

def convert_text_to_img(
        lines, save_path,
        fnt_size=20,
        fnt_ratio=0.6,
        fnt_path=os.path.join(os.getenv('HOME'), '.local/share/fonts/IBM-Plex-Mono/IBMPlexMono-Bold.ttf')
):
    cols = max(len(line) for line in lines)
    rows = len(lines)
    img_sz = (20 * 2 + cols * int(fnt_size * fnt_ratio), 20 * 2 + rows * fnt_size)
    # MAX_DIMENSION = 65000 # MAX is 65500
    # if max(img_sz) > MAX_DIMENSION
    #     # TODO 

    # mode "1" for black and white
    img = Image.new("1", img_sz)
    fnt = ImageFont.truetype(fnt_path, fnt_size)
    d = ImageDraw.Draw(img)

    for idx, line in enumerate(lines):
        d.text((20, 20 + idx * fnt_size), line, font=fnt, fill=255)
    img.save(save_path)
    img.close()

def parse_str_date(date_to_parse, source_date=None):
    cal = pdt.Calendar()

    # The source_date is a time_struct
    if not source_date:
       source_date = dt.datetime.today().date().timetuple()
    else:
        if isinstance(source_date, (dt.datetime, dt.date)):
            source_date = source_date.timetuple()

    try:
        date = dt.date(*cal.parseDate(date_to_parse, source_date)[:3])
    except ValueError:
        time_struct = cal.parse(date_to_parse, source_date)[0]
        date = dt.date(*time_struct[:3])


    return date
    
def send_pushover_notification(message, title="", files=dict()):
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")

    data = {
            "token": token,
            "user": user,
            "message": message,
        }
    if title:
        data['title'] = title

    r = requests.post(
        "https://api.pushover.net/1/messages.json",
        data = data,
        files=files)

    return r

    # conn = http.client.HTTPSConnection("api.pushover.net:443")
    # conn.request("POST", "/1/messages.json",
    #              urllib.parse.urlencode({
    #                  "token": token,
    #                  "user": user,
    #                  "message": message,
    #                  "title": title
    #              }), { "Content-type": "application/x-www-form-urlencoded" })
    # conn.getresponse()
