from sqlalchemy import Column, Integer, String, Date

from db.setting import Engine
from db.setting import Base

class Stadium(Base):
    """
    支部テーブル

    id: Integer [PK]
        支部番号

    stadium_name: String
        競艇場名
    motor_change_timing: Date
        モーター交換時期
    boat_change_timing: Date
        ボート交換時期

    """

    __tablename__ = 'stadium'
    __table_args__ = {
        'comment': '支部'
    }

    id = Column(Integer, primary_key=True)
    stadium_name = Column(String)
    motor_change_timing = Column(Date)
    boat_change_timing = Column(Date)


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)