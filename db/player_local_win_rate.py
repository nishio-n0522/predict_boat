from datetime import date

from sqlalchemy import Column, Integer, Float, ForeignKey, Date
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import relationship

import db
from db.db_setting import Base


class PlayerLocalWinRate(Base):
    """
    選手当地勝率テーブル

    id: Integer [PK]

    player_id: Integer
        モーター番号
    race_date: Date
        レース開催日
    latest_win_rate: Float
        最新勝率
    latest_top2finish_rate: Float
        最新2着以内率

    """

    __tablename__ = 'player_local_win_rate'
    __table_args__ = {
        'comment': '選手当地勝率'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("player.id"))
    stadium_id = Column(Integer, ForeignKey("stadium.id"))
    race_date = Column(Date)
    latest_win_rate = Column(Float)
    latest_top2finish_rate = Column(Float)

    player = relationship("Player", backref="player_local_win_rate")

    def __init__(self, player_id: int, stadium_id: int, race_date: date, latest_win_late: float, latest_top2finish_rate: float):
        self.player_id = player_id
        self.stadium_id = stadium_id
        self.race_date = race_date
        self.latest_win_rate = latest_win_late
        self.latest_top2finish_rate = latest_top2finish_rate

def get_or_create_motor(session: Session, player_id: int, stadium_id: int, race_date: date, latest_win_rate: float, latest_top2finish_rate: float):
    player_local_win_rate = session.query(PlayerLocalWinRate).filter_by(player_id=player_id, stadium_id=stadium_id, race_date=race_date).one_or_none()
    if player_local_win_rate is None:
        player_local_win_rate = PlayerLocalWinRate(player_id, stadium_id, race_date, latest_win_rate,latest_top2finish_rate)
        session.add(player_local_win_rate)
        session.commit()
