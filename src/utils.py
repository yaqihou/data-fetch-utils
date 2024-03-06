
import os
import datetime as dt
import parsedatetime as pdt

from PIL import Image, ImageDraw, ImageFont


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

    # mode "1" for black and white
    img = Image.new("1", (20 * 2 + cols * int(fnt_size * fnt_ratio), 20 * 2 + rows * fnt_size))
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
    
