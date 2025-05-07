from sqlalchemy import Column, String
from database import Base

class School(Base):
    __tablename__ = "school_tb"

    sch_cd = Column(String(50), primary_key=True)
    sch_name = Column(String(255))
