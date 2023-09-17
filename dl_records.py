from time import sleep
from datetime import datetime as dt
from datetime import timedelta as td
from pathlib import Path

from requests import get


START_DATE = "2020-04-01"
END_DATE = "2023-09-06"

SAVE_DIR = Path("./data/competitive_record")

INTERVAL = 3

FIXED_URL = "http://www1.mbrace.or.jp/od2/K/"

print("作業を開始します")

if not SAVE_DIR.exists():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

start_date = dt.strptime(START_DATE, '%Y-%m-%d')
end_date = dt.strptime(END_DATE, '%Y-%m-%d')

days_num = (end_date - start_date).days + 1

date_list = []

for i in range(days_num):
    target_date = start_date + td(days=i)
    date_list.append(target_date.strftime("%Y%m%d"))

for date in date_list:
    yyyymm = date[0:4] + date[4:6]
    yymmdd = date[2:4] + date[4:6] + date[6:8]

    variable_url = FIXED_URL + yyyymm + "/k" + yymmdd + ".lzh"
    file_name = "k" + yymmdd + ".lzh"

    r = get(variable_url)

    if r.status_code == 200:
        with open(SAVE_DIR / file_name, "wb") as file:
            file.write(r.content)
        print(variable_url + " をダウンロードしました")

    else:
        print(variable_url + " のダウンロードに失敗しました")

    sleep(INTERVAL)

print("作業を終了しました")