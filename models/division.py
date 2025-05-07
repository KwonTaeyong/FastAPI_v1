from sqlalchemy import Column, Integer, String
from database import Base

class Division(Base):
    __tablename__ = "division_tb"

    div_cd = Column(Integer, primary_key=True, index=True)
    div_name = Column(String(100))
    div_yn = Column(Integer)
