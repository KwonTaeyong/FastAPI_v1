from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base

class Member(Base):
    __tablename__ = "member_tb"

    mb_no = Column(Integer, primary_key=True, index=True)
    mb_id = Column(String(50), nullable=False)
    mb_pwd = Column(String(100), nullable=False)
    insert_dt = Column(DateTime, default=func.now())
    update_dt = Column(DateTime, default=func.now(), onupdate=func.now())
