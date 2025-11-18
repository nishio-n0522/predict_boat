from sqlalchemy import Column, Integer, Float, Date, Time, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session

from db.db_setting import Base


class LiveInfo(Base):
    """
    直前情報テーブル

    レース直前の各艇の情報を記録

    id: Integer [PK]
        主キー
    stadium_id: Integer [FK]
        競艇場ID
    date: Date
        レース開催日
    race_index: Integer
        レース番号
    boat_number: Integer
        艇番
    player_id: Integer [FK]
        選手登番
    exhibition_time: Float
        展示タイム（秒）
    tilt: Float
        チルト（角度）
    approach_course: Integer
        進入コース（予想）
    start_exhibition: String
        スタート展示の評価
    motor_adjustment: String
        モーター調整内容
    body_weight: Float
        体重（kg）
    adjusted_weight: Float
        調整体重（kg）
    win_odds: Float
        単勝オッズ
    quinella_odds: Float
        2連複オッズ（最小値）
    """

    __tablename__ = 'live_info'
    __table_args__ = {
        'comment': '直前情報'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    stadium_id = Column(Integer, ForeignKey("stadium.id"))
    date = Column(Date)
    race_index = Column(Integer)
    boat_number = Column(Integer)
    player_id = Column(Integer, ForeignKey("player.id"))
    exhibition_time = Column(Float, nullable=True)
    tilt = Column(Float, nullable=True)
    approach_course = Column(Integer, nullable=True)
    start_exhibition = Column(String, nullable=True)
    motor_adjustment = Column(String, nullable=True)
    body_weight = Column(Float, nullable=True)
    adjusted_weight = Column(Float, nullable=True)
    win_odds = Column(Float, nullable=True)
    quinella_odds = Column(Float, nullable=True)

    stadium = relationship("Stadium", backref="live_info")
    player = relationship("Player", backref="live_info")

    def __init__(self,
                 stadium,
                 date,
                 race_index,
                 boat_number,
                 player,
                 exhibition_time=None,
                 tilt=None,
                 approach_course=None,
                 start_exhibition=None,
                 motor_adjustment=None,
                 body_weight=None,
                 adjusted_weight=None,
                 win_odds=None,
                 quinella_odds=None):

        self.stadium = stadium
        self.date = date
        self.race_index = race_index
        self.boat_number = boat_number
        self.player = player
        self.exhibition_time = exhibition_time
        self.tilt = tilt
        self.approach_course = approach_course
        self.start_exhibition = start_exhibition
        self.motor_adjustment = motor_adjustment
        self.body_weight = body_weight
        self.adjusted_weight = adjusted_weight
        self.win_odds = win_odds
        self.quinella_odds = quinella_odds


def create_and_get(session: Session, **kwargs):
    """
    直前情報レコードを作成してデータベースに保存

    Args:
        session: SQLAlchemyセッション
        **kwargs: LiveInfoの初期化パラメータ

    Returns:
        作成されたLiveInfoオブジェクト
    """
    try:
        live_info = LiveInfo(**kwargs)
    except Exception as e:
        raise Exception(e, kwargs)
    session.add(live_info)
    session.commit()
    return live_info


def get_or_create(session: Session, **kwargs):
    """
    直前情報レコードを取得、存在しない場合は作成

    Args:
        session: SQLAlchemyセッション
        **kwargs: 検索・作成用のパラメータ

    Returns:
        LiveInfoオブジェクトとbool（新規作成されたかどうか）のタプル
    """
    # 既存レコードを検索
    instance = session.query(LiveInfo).filter_by(
        stadium_id=kwargs.get('stadium').id if 'stadium' in kwargs else kwargs.get('stadium_id'),
        date=kwargs.get('date'),
        race_index=kwargs.get('race_index'),
        boat_number=kwargs.get('boat_number')
    ).first()

    if instance:
        # 既存レコードを更新
        for key, value in kwargs.items():
            if key not in ['stadium', 'date', 'race_index', 'boat_number'] and value is not None:
                if key == 'player' and hasattr(value, 'id'):
                    setattr(instance, 'player_id', value.id)
                    instance.player = value
                else:
                    setattr(instance, key, value)
        session.commit()
        return instance, False
    else:
        return create_and_get(session, **kwargs), True
