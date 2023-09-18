from sqlalchemy import Column, Integer, String, Float, Date, Text, Numeric

from db.setting import Engine
from db.setting import Base

class BoatRaceData(Base):
    """
    レース結果

    stadium_id: Integer
        ボートレース場id
    date: Date
        レース開催日
    race_inedex: Integer
        レース番号
    series_name: Text
        節名
    weather_id: Integer
        天気id
    wind_direction_id: Integer
        風向id
    wind_speed: Float
        風速 [m/s]
    wave_height: Float
        波高
    win_refund: Integer
        単勝払い戻し
    place_refund: Integer
        複勝払い戻し
    perfecta_refund: Integer
        2連単払い戻し
    quinella_refund: Integer
        2連複払い戻し
    boxed_quinella_refund: Integer
        拡連複払い戻し
    trifecta_refund: Integer
        3連単払い戻し
    boxed_trifecta_refund: Integer
        3連複払い戻し
    
    """

    __tablename__ = 'race_results'
    __table_args__ = {
        'comment': '各レースの条件と結果のテーブル'
    }

    stadium_id = Column('stadium_id', Integer, primary_key=True)
    date = Column('date', Date, primary_key=True)
    race_index = Column('race_index', Integer, primary_key=True)
    series_name = Column('series_name', Text)
    weather = Column('weather', Text)
    wind_direction = Column('wind_direction', Text)
    wind_speed = Column('wind_speed', Float)
    wave_height = Column('wave_height', Float)
    win_refund = Column('win_refund', Integer)
    place_refund = Column('place_refund', Integer)
    perfecta_refund = Column('perfecta_refund', Integer)
    quinella_refund = Column('quinella_refund', Integer)
    boxed_quinella_refund = Column('boxed_quinella_refund', Integer)
    trifecta_refund = Column('trifecta_refund', Integer)
    boxed_trifecta_refund = Column('boxed_trifecta_refund', Integer)


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)