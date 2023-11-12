# SQLチートシート
# https://qiita.com/riita10069/items/f2df509c31d89eeed36e

# SQLチュートリアル
# https://sqlzoo.net/wiki/SELECT_basics

# SQLAlchemy参考
# https://qiita.com/arkuchy/items/75799665acd09520bed2

# pandas参考
# https://cpp-learning.com/sqlalchemy-pandas/
# https://qiita.com/ysdyt/items/9ccca82fc5b504e7913a

# 使用するライブラリをインポート
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select

import db

# sqliteへ接続
engine = create_engine("sqlite:///sqlite.sqlite3")

Session = sessionmaker(bind=engine)
session = Session()

# SELECT
results = session.query(
    db.each_race_results.EachRaceResult
    ).filter(
        db.each_race_results.EachRaceResult.win_refund>=5000
    ).all()

for result in results:
  print(result.date, result.stadium_id, result.race_index, result.win_refund)


session.close()