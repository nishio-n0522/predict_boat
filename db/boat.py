from sqlalchemy import Column, Integer, Float, ForeignKey

from db.setting import Engine
from db.setting import Base

class Boat(Base):
    """
    ボートテーブル

    id: Integer [PK]

    boat_number: Integer
        ボート番号
    stadium_id: Integer [FK]
        支部id
    latest_top2finish_rate: Float
        最新2着以内率

    """

    __tablename__ = 'boat'
    __table_args__ = {
        'comment': 'ボート'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    boat_number = Column(Integer)
    stadium_id = Column(Integer, ForeignKey("stadium.id"))
    latest_top2finish_rate = Column(Float)

if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)