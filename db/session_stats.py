from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session

from db.db_setting import Base


class SessionStats(Base):
    """
    節間成績テーブル

    各選手の節間（開催期間中）の成績を記録

    id: Integer [PK]
        主キー
    stadium_id: Integer [FK]
        競艇場ID
    date: Date
        レース開催日
    player_id: Integer [FK]
        選手登番
    session_1st_rate: Float
        節間1着率
    session_2nd_rate: Float
        節間2着率
    session_3rd_rate: Float
        節間3着率
    session_win_rate: Float
        節間勝率
    session_race_count: Integer
        節間出走回数
    session_1st_count: Integer
        節間1着回数
    session_2nd_count: Integer
        節間2着回数
    session_3rd_count: Integer
        節間3着回数
    """

    __tablename__ = 'session_stats'
    __table_args__ = {
        'comment': '節間成績'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    stadium_id = Column(Integer, ForeignKey("stadium.id"))
    date = Column(Date)
    player_id = Column(Integer, ForeignKey("player.id"))
    session_1st_rate = Column(Float, nullable=True)
    session_2nd_rate = Column(Float, nullable=True)
    session_3rd_rate = Column(Float, nullable=True)
    session_win_rate = Column(Float, nullable=True)
    session_race_count = Column(Integer, nullable=True)
    session_1st_count = Column(Integer, nullable=True)
    session_2nd_count = Column(Integer, nullable=True)
    session_3rd_count = Column(Integer, nullable=True)

    stadium = relationship("Stadium", backref="session_stats")
    player = relationship("Player", backref="session_stats")

    def __init__(self,
                 stadium,
                 date,
                 player,
                 session_1st_rate=None,
                 session_2nd_rate=None,
                 session_3rd_rate=None,
                 session_win_rate=None,
                 session_race_count=None,
                 session_1st_count=None,
                 session_2nd_count=None,
                 session_3rd_count=None):

        self.stadium = stadium
        self.date = date
        self.player = player
        self.session_1st_rate = session_1st_rate
        self.session_2nd_rate = session_2nd_rate
        self.session_3rd_rate = session_3rd_rate
        self.session_win_rate = session_win_rate
        self.session_race_count = session_race_count
        self.session_1st_count = session_1st_count
        self.session_2nd_count = session_2nd_count
        self.session_3rd_count = session_3rd_count


def create_and_get(session: Session, **kwargs):
    """
    節間成績レコードを作成してデータベースに保存

    Args:
        session: SQLAlchemyセッション
        **kwargs: SessionStatsの初期化パラメータ

    Returns:
        作成されたSessionStatsオブジェクト
    """
    try:
        session_stats = SessionStats(**kwargs)
    except Exception as e:
        raise Exception(e, kwargs)
    session.add(session_stats)
    session.commit()
    return session_stats


def get_or_create(session: Session, **kwargs):
    """
    節間成績レコードを取得、存在しない場合は作成

    Args:
        session: SQLAlchemyセッション
        **kwargs: 検索・作成用のパラメータ

    Returns:
        SessionStatsオブジェクトとbool（新規作成されたかどうか）のタプル
    """
    # 既存レコードを検索
    instance = session.query(SessionStats).filter_by(
        stadium_id=kwargs.get('stadium').id if 'stadium' in kwargs else kwargs.get('stadium_id'),
        date=kwargs.get('date'),
        player_id=kwargs.get('player').id if 'player' in kwargs else kwargs.get('player_id')
    ).first()

    if instance:
        return instance, False
    else:
        return create_and_get(session, **kwargs), True
