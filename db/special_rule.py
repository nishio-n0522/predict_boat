from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.session import Session

from db.db_setting import Engine
from db.db_setting import Base

class SpecialRule(Base):
    """
    特別ルールテーブル

    id: Integer [PK]

    special_rule: String
        特別ルール名

    """

    __tablename__ = 'special_rule'
    __table_args__ = {
        'comment': '特別ルール'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    special_rule_name = Column(String)

    def __init__(self, special_rule_name):
        self.special_rule_name = special_rule_name

def get_or_create(session: Session, special_rule_name: str):
    special_rule = session.query(SpecialRule).filter_by(special_rule_name=special_rule_name).one_or_none()
    if special_rule is None:
        special_rule = SpecialRule(special_rule_name)
        session.add(special_rule)
        session.commit()
    return special_rule
