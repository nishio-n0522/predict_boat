from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session

from db.db_setting import Base

class EachRaceResult(Base):
    """
    各レース結果テーブル

    id: Integer [PK]

    stadium_id: Integer [FK]
        支部id
    date: Date
        レース開催日
    race_index: Integer
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
    boxed_quinella_refund1: Integer
        拡連複払い戻し 円
    boxed_quinella_refund2: Integer
        拡連複払い戻し 円
    boxed_quinella_refund3: Integer
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
    race_index = Column(Integer)
    race_name = Column(String)
    weather_id = Column(Integer, ForeignKey("weather.id"))
    wind_direction_id = Column(String, ForeignKey('wind_direction.id'))
    special_rule_id = Column(Integer, ForeignKey("special_rule.id"))
    wind_speed = Column(Float)
    wave_height = Column(Float)
    decisive_factor_id = Column(Integer, ForeignKey("decisive_factor.id"))
    win_refund = Column(Integer, nullable=True)
    place_refund = Column(Integer, nullable=True)
    perfecta_refund = Column(Integer, nullable=True)
    quinella_refund = Column(Integer, nullable=True)
    boxed_quinella_refund1 = Column(Integer, nullable=True)
    boxed_quinella_refund2 = Column(Integer, nullable=True)
    boxed_quinella_refund3 = Column(Integer, nullable=True)
    trifecta_refund = Column(Integer, nullable=True)
    boxed_trifecta_refund = Column(Integer, nullable=True)

    stadium = relationship("Stadium", backref="each_race_result")
    # each_boat_data = relationship("EachBoatData", backref="each_race_result")
    special_rule = relationship("SpecialRule", backref="each_race_result")
    weather = relationship("Weather", backref="each_race_result")
    wind_direction = relationship("WindDirection", backref="each_race_result")
    decisive_factor = relationship("DecisiveFactor", backref="each_race_result")


    def __init__(self,
                 stadium, 
                 date, 
                 race_index,
                 race_name,
                 special_rule,
                 weather,
                 wind_direction,
                 wind_speed,
                 wave_height,
                 decisive_factor,
                 win_refund=None,
                 place_refund=None,
                 perfecta_refund=None,
                 quinella_refund=None,
                 boxed_quinella_refund1=None,
                 boxed_quinella_refund2=None,
                 boxed_quinella_refund3=None,
                 trifecta_refund=None,
                 boxed_trifecta_refund=None):
        
        self.stadium = stadium
        self.date = date
        self.race_index = race_index
        self.race_name = race_name
        self.special_rule = special_rule
        self.weather = weather
        self.wind_direction = wind_direction
        self.wind_speed = wind_speed
        self.wave_height = wave_height
        self.decisive_factor = decisive_factor
        self.win_refund = win_refund
        self.place_refund = place_refund
        self.perfecta_refund = perfecta_refund
        self.quinella_refund = quinella_refund
        self.boxed_quinella_refund1 = boxed_quinella_refund1
        self.boxed_quinella_refund2 = boxed_quinella_refund2
        self.boxed_quinella_refund3 = boxed_quinella_refund3
        self.trifecta_refund = trifecta_refund
        self.boxed_trifecta_refund = boxed_trifecta_refund

def create_and_get(session: Session, **kwargs):
    try:
        each_race_result = EachRaceResult(**kwargs)
    except Exception as e:
        raise Exception(e, kwargs)
    session.add(each_race_result)
    session.commit()
    return each_race_result