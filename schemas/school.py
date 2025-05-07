from pydantic import BaseModel

class SchoolOut(BaseModel):
    sch_cd: str
    sch_name: str

    class Config:
        orm_mode = True
