from sqlalchemy import Column, Integer, String
from database import Base

class Container(Base):
    __tablename__ = "container_tb"

    
    container_cd = Column(Integer, primary_key=True, autoincrement=True) 
    sch_cd = Column(Integer, nullable=False)
    sch_name = Column(String(100), nullable=False)
    sch_nickname = Column(String(100))
    domain = Column(String(255))
    grop_cd = Column(Integer, nullable=False)
    div_cd = Column(Integer, nullable=False)
    # div_name = Column(String(100))