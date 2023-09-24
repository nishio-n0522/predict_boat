from sqlalchemy import Column, Integer, String, Float, Date, Text, Numeric

from db.setting import Engine
from db.setting import Base

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

if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)