from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session

from db.db_setting import Engine
from db.db_setting import Base

change_boat_timing_dict = {
    "戸田": 7,
    "江戸川": 4,
    "平和島": 6,
    "多摩川": 8,
    "蒲郡": 5,
    "三国": 4,
    "琵琶湖": 6,
    "住之江": 3,
    "尼崎": 4,
    "鳴門": 4,
    "宮島": 9,
    "下関": 2,
    "福岡": 6,
    "桐生": 10,
    "浜名湖": 9,
    "常滑": 7,
    "津": 8,
    "丸亀": 7,
    "児島": 3,
    "徳山": 11,
    "若松": 6,
    "芦屋": 4,
    "唐津": 4,
    "大村": 7,
}

change_motor_timing_dict = {
    "戸田": 7,
    "江戸川": 4,
    "平和島": 6,
    "多摩川": 8,
    "蒲郡": 5,
    "三国": 4,
    "琵琶湖": 6,
    "住之江": 3,
    "尼崎": 4,
    "鳴門": 4,
    "宮島": 9,
    "下関": 2,
    "福岡": 6,
    "桐生": 12,
    "浜名湖": 4,
    "常滑": 12,
    "津": 9,
    "丸亀": 11,
    "児島": 1,
    "徳山": 4,
    "若松": 12,
    "芦屋": 5,
    "唐津": 8,
    "大村": 3,
}

branch_dict = {
    "桐生": "群馬",
    "戸田": "埼玉",
    "江戸川": "東京",
    "平和島": "東京",
    "多摩川": "東京",
    "浜名湖": "静岡",
    "蒲郡": "愛知",
    "常滑": "愛知",
    "津": "三重",
    "三国": "福井",
    "琵琶湖": "滋賀",
    "住之江": "大阪",
    "尼崎": "兵庫",
    "鳴門": "徳島",
    "丸亀": "香川",
    "児島": "岡山",
    "宮島": "広島",
    "徳山": "山口",
    "下関": "山口",
    "若松": "福岡",
    "芦屋": "福岡",
    "福岡": "福岡",
    "唐津": "佐賀",
    "大村": "長崎",
}

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
    branch_name = Column(String)
    motor_change_timing = Column(Integer)
    boat_change_timing = Column(Integer)

    def __init__(self, id: int, stadium_name: str):
        self.id = id
        self.stadium_name = stadium_name
        self.branch_name = branch_dict[stadium_name]
        self.motor_change_timing = change_motor_timing_dict[stadium_name]
        self.boat_change_timing = change_boat_timing_dict[stadium_name]

def get_or_create(session: Session, stadium_id: int, stadium_name: str):
    stadium = session.query(Stadium).filter_by(id=stadium_id).one_or_none()
    if stadium is None:
        stadium = Stadium(stadium_id, stadium_name)
        session.add(stadium)
        session.commit()
    return stadium
