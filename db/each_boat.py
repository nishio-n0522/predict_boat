from sqlalchemy import Column, Integer, String, Float, Date, Text, Numeric

from db.setting import Engine
from db.setting import Base

class EachBoatData(Base):
    """
    各艇番レースデータ

    stadium_id: Integer
        ボートレース場id
    date: Text
        レース日
    race_index: Integer
        レース番号
    boat_number: Integer
        艇番
    player_id: Integer
        選手登番
    motor_number: Integer
        モーター番号
    boat_number: Integer
        ボート番号
    goal_number: Integer
        着順
    start_number: Integer
        進入
    sample_time: Float
        展示タイム
    start_timing: Float
        スタートタイミング
    race_time: Float
        レースタイム

    """

    __tablename__ = 'each_boat_data'
    __table_args__ = {
        'comment': '各艇番レースデータ'
    }

    stadium_id = Column('stadium_id', Integer, primary_key=True)
    date = Column('date', Text, primary_key=True)
    race_index = Column('race_index', Integer, primary_key=True)
    boat_number = Column('boat_number', Integer, primary_key=True)
    player_id = Column('player_id', Integer)
    motor_number = Column('motor_number', Integer)
    boat_number = Column('boat_number', Integer)
    goal_number = Column('goal_number', Integer)
    start_number = Column('start_number', Integer)
    sample_time = Column('sample_time', Float)
    start_timing = Column('start_timing', Float)
    race_time = Column('race_time', Float)


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)