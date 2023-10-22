import datetime as dt

from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session

import db
from db.db_setting import Base

class Motor(Base):
    """
    モーターテーブル

    id: Integer [PK]

    motor_number: Integer
        モーター番号
    stadium_id: Integer
        支部id

    """

    __tablename__ = 'motor'
    __table_args__ = {
        'comment': 'モーター'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    motor_number = Column(Integer)
    stadium_id = Column(Integer, ForeignKey("stadium.id"))
    
    stadium = relationship("Stadium", backref="motor")

    def __init__(self, motor_number, stadium):
        self.motor_number = motor_number
        self.stadium = stadium

def get_or_create(session: Session, motor_number: int, stadium: db.stadium.Stadium, latest_top2finish_rate: float):
    motor = session.query(Motor).filter_by(motor_number=motor_number, stadium=stadium).first()
    if latest_top2finish_rate == 0 or motor == None:
        motor = Motor(motor_number, stadium)
        session.add(motor)
        session.commit()
    return motor

def get(session: Session, motor_number: int, stadium: db.stadium.Stadium):
    motor = session.query(Motor).filter_by(motor_number=motor_number, stadium=stadium).first()
    # if motor == None:
    #     motor = Motor(motor_number, stadium)
    #     session.add(motor)
    #     session.commit()
    return motor
