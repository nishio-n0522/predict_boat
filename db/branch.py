from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.session import Session

from db.db_setting import Engine
from db.db_setting import Base

class Branch(Base):
    """
    支部テーブル

    id: Integer [PK]

    branch: String
        支部名

    """

    __tablename__ = 'branch'
    __table_args__ = {
        'comment': '支部'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_name = Column(String)

    def __init__(self, branch_name):
        self.branch_name = branch_name

def get_or_create(session: Session, branch_name: str):
    branch = session.query(Branch).filter_by(branch_name=branch_name).one_or_none()
    if branch is None:
        branch = Branch(branch_name)
        session.add(branch)
        session.commit()
    return branch
