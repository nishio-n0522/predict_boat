from sqlalchemy import Column, Integer, String

from db.db_setting import Engine
from db.db_setting import Base

class Weather(Base):
    """
    天候テーブル

    id: Integer [PK]

    weather_name: String
        天候名

    """

    __tablename__ = 'weather'
    __table_args__ = {
        'comment': '天候'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    weather_name = Column(String)

    def __init__(self, weather_name):
        self.weather_name = weather_name

def get_or_create_weather(session, weather_name):
    weather = session.query(Weather).filter_by(weather_name).one_or_none()
    if weather is None:
        weather = Weather(weather_name)
        session.add(weather)
        session.commit()
    return weather
