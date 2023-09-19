from sqlalchemy import Column, Integer, String, Float, Date, Text, Numeric

from db.setting import Engine
from db.setting import Base

class Player(Base):
    """
    選手データテーブル

    player_id: Integer
        選手登番
    name: Text
        名前
    age: Integer
        年齢
    stadium_id: Integer
        ボートレース場id
    weight: Float
        体重
    grade: Text
        級別
    latest_national_win_rate: Float
        最新全国勝率
    latest_national_top2finish_rate: Float
        最新全国2着以内勝率
    latest_local_win_rate: Float
        最新当地勝率
    latest_local_top2finish_rate: Float
        最新当地2着以内勝率

    """

    __tablename__ = 'weather'
    __table_args__ = {
        'comment': '天気の種類を管理するテーブル'
    }

    player_id = Column('player_id', Integer, primary_key=True)
    name = Column('name', Text)
    age = Column('age', Integer)
    stadium_id = Column('stadium_id', Integer)
    weight = Column('weight', Float)
    grade = Column('grade', Text)
    latest_national_win_rate = Column('latest_national_win_rate', Float)
    latest_national_top2finish_rate = Column('latest_national_top2finish_rate', Float)
    latest_local_win_rate = Column('latest_local_win_rate', Float)
    latest_local_top2finish_rate = Column('latest_local_top2finish_rate', Float)


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)