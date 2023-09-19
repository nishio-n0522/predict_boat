from sqlalchemy import Column, Integer, String, Float, Date, Text, Numeric

from db.setting import Engine
from db.setting import Base

class WindDirectionType(Base):
    """
    風向きテーブル

    wind_direction_id: Integer
        風向id
    wind_direction_type: Text
        風向き

    """

    __tablename__ = 'wind_direction_type'
    __table_args__ = {
        'comment': '風向きを管理するテーブル'
    }

    wind_direction_id = Column('wind_direction_id', Integer, primary_key=True)
    wind_direction_type = Column('wind_direction_type', Text)


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)