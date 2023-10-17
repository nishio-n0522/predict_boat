from sqlalchemy import Column, Integer, String, Float, Date, Text, Numeric

from db.db_setting import Engine
from db.db_setting import Base

class WindDirection(Base):
    """
    風向きテーブル

    id: Integer [PK]

    wind_direction_name: String
        風向き名

    """

    __tablename__ = 'wind_direction'
    __table_args__ = {
        'comment': '風向き名'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    wind_direction_name = Column(String)

    def __init__(self, wind_direction_name):
        self.wind_direction_name = wind_direction_name

def get_or_create_wind_direction(session, wind_direction_name):
    wind_direction = session.query(WindDirection).filter_by(wind_direction_name).one_or_none()
    if wind_direction is None:
        wind_direction = WindDirection(wind_direction_name)
        session.add(wind_direction)
        session.commit()
    return wind_direction

