from sqlalchemy.orm import Session
from models.member import Member
from schemas.member import MemberCreate


def get_members(db: Session):
    return db.query(Member).all()
