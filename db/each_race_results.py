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

    def __init__(self, 
                 stadium_id, 
                 date, 
                 nth_race,
                 race_name,
                 weather_id,
                 wind_direction_id,
                 wind_speed,
                 wave_height,
                 decisive_factor_id,
                 win_refund,
                 place_refund,
                 perfecta_refund,
                 quinella_refund,
                 boxed_quinella_refund,
                 trifecta_refund,
                 boxed_trifecta_refund):
        
        self.stadium_id = stadium_id
        self.date = date
        self.nth_race = nth_race
        self.race_name = race_name
        self.weather_id = weather_id
        self.wind_direction_id = wind_direction_id
        self.wind_speed = wind_speed
        self.wave_height = wave_height
        self.decisive_factor_id = decisive_factor_id
        self.win_refund = win_refund
        self.place_refund = place_refund
        self.perfecta_refund = perfecta_refund
        self.quinella_refund = quinella_refund
        self.boxed_quinella_refund = boxed_quinella_refund
        self.trifecta_refund = trifecta_refund
        self.boxed_trifecta_refund = boxed_trifecta_refund

    


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)