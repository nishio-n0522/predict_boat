from sqlalchemy import Column, Integer, Float, ForeignKey

from db.db_setting import Engine
from db.db_setting import Base

class Motor(Base):
    """
    モーターテーブル

    id: Integer [PK]

    motor_number: Integer
        モーター番号
    stadium_id: Integer
        支部id
    latest_top2finish_rate: Float
        最新2着以内率

    """

    __tablename__ = 'motor'
    __table_args__ = {
        'comment': 'モーター'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    motor_number = Column(Integer)
    stadium_id = Column(Integer, ForeignKey("stadium.id"))
    latest_top2finish_rate = Column(Float)

    def __init__(self, motor_number, stadium_id, latest_top2finish_rate):
        self.motor_number = motor_number
        self.stadium_id = stadium_id
        self.latest_top2finish_rate = latest_top2finish_rate

def get_or_create_motor(session, *args):
    motor_number = args[0]

    motor = session.query(Motor).filter_by(motor_number).one_or_none()
    if motor is None:
        motor = Motor(args)
        session.add(motor)
        session.commit()
    return motor
