from sqlalchemy import Column, Integer, TIME,  String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session

from db.db_setting import Base

class EachBoatData(Base):
    """
    各艇番データテーブル

    id: Integer [PK]

    boat_number: String
        艇番
    race_id: Integer [FK]
        レースid
    player_id: Integer [FK]
        選手登番
    motor_id: Integer [FK]
        モーターid
    boat_id: Integer [FK]
        ボートid
    order_of_arrival: Integer
        着順
    starting order: Integer
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
        'comment': '各艇番データ'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    boat_number = Column(Integer)
    each_race_result_id = Column(Integer, ForeignKey("each_race_result.id"))
    player_id = Column(Integer, ForeignKey("player.id"))
    motor_id = Column(Integer, ForeignKey("motor.id"))
    boat_id = Column(Integer, ForeignKey("boat.id"))
    order_of_arrival = Column(Integer, nullable=True)
    starting_order = Column(Integer, nullable=True)
    sample_time = Column(Float, nullable=True)
    start_timing = Column(Float, nullable=True)
    race_time = Column(TIME, nullable=True)

    each_race_result = relationship("EachRaceResult", backref="each_boat_data")
    player = relationship("Player", backref="each_boat_data")
    motor = relationship("Motor", backref="each_boat_data")
    boat = relationship("Boat", backref="each_boat_data")

    def __init__(self, 
                 boat_number, 
                 each_race_result, 
                 player,
                 motor,
                 boat,
                 order_of_arrival,
                 starting_order,
                 sample_time,
                 start_timing,
                 race_time):
        
        self.boat_number = boat_number
        self.each_race_result = each_race_result
        self.player = player
        self.motor = motor
        self.boat = boat
        self.order_of_arrival = order_of_arrival
        self.starting_order = starting_order
        self.sample_time = sample_time
        self.start_timing = start_timing
        self.race_time = race_time

def create(session: Session, **kwargs):
    each_boat_data = EachBoatData(**kwargs)
    session.add(each_boat_data)
    session.commit()
