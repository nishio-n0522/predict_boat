from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey

from db.setting import Engine
from db.setting import Base

class EachRaceResult(Base):
    """
    各レース結果テーブル

    id: Integer [PK]

    stadium_id: Integer [FK]
        支部id
    date: Date
        レース開催日
    nth_race: Integer
        レース番号
    race_name: String
        レース名
    weather_id: Integer [FK]
        天気id
    wind_direction_id: Integer [FK]
        風向id
    wind_speed: Float
        風速 m/s
    wave_height: Float
        波高 cm
    decisive_factor_id: String [FK]
        決まり手
    win_refund: Integer
        単勝払い戻し 円
    place_refund: Integer
        複勝払い戻し 円
    perfecta_refund: Integer
        2連単払い戻し 円
    quinella_refund: Integer
        2連複払い戻し 円
    boxed_quinella_refund: Integer
        拡連複払い戻し 円
    trifecta_refund: Integer
        3連単払い戻し 円
    boxed_trifecta_refund: Integer
        3連複払い戻し 円
    
    """

    __tablename__ = 'each_race_result'
    __table_args__ = {
        'comment': '各レース結果'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    stadium_id = Column(Integer, ForeignKey("stadium.id"))
    date = Column(Date)
    nth_race = Column(Integer)
    race_name = Column(String)
    weather_id = Column(Integer, ForeignKey("weather.id"))
    wind_direction_id = Column(String, ForeignKey('wind_direction.id'))
    wind_speed = Column(Float)
    wave_height = Column(Float)
    decisive_factor_id = Column(Integer, ForeignKey("decisive_factor.id"))
    win_refund = Column(Integer)
    place_refund = Column(Integer)
    perfecta_refund = Column(Integer)
    quinella_refund = Column(Integer)
    boxed_quinella_refund = Column(Integer)
    trifecta_refund = Column(Integer)
    boxed_trifecta_refund = Column(Integer)


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)