from datetime import date

from sqlalchemy import Column, Integer, Float, ForeignKey, Date
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import relationship

from db.player import Player
from db.db_setting import Base


class PlayerNationalWinRate(Base):
    """
    選手全国勝率テーブル

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

    __tablename__ = 'player_national_win_rate'
    __table_args__ = {
        'comment': '選手全国勝率'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("player.id"), index=True)
    race_date = Column(Date, index=True)
    latest_win_rate = Column(Float)
    latest_top2finish_rate = Column(Float)

    player = relationship("Player", backref="player_national_win_rate")

    def __init__(self, player: Player, race_date: date, latest_win_late: float, latest_top2finish_rate: float):
        self.player = player
        self.race_date = race_date
        self.latest_win_rate = latest_win_late
        self.latest_top2finish_rate = latest_top2finish_rate

def create(session: Session, player: Player, race_date: date, latest_win_rate: float, latest_top2finish_rate: float):
    player_national_win_rate = session.query(PlayerNationalWinRate).filter_by(player=player, race_date=race_date).one_or_none()
    if player_national_win_rate is None:
        player_national_win_rate = PlayerNationalWinRate(player, race_date, latest_win_rate, latest_top2finish_rate)
        session.add(player_national_win_rate)
        # session.commit()
