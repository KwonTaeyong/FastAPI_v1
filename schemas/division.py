from pydantic import BaseModel

class DivisionCreate(BaseModel):
    div_cd: int
    div_name: str
    div_yn: int
    
    class Config:
        from_attributes = True
   
class DivisionUpdate(BaseModel):
    div_cd: int  # 또는 str, DB 타입에 따라
    div_name: str
    div_yn: int
     
class DivisionDelete(BaseModel):
    div_cd: int
    div_name: str
    div_yn: int
    
class DivisionOut(BaseModel):
    div_cd: int
    div_name: str
    div_yn: int

    class Config:
        from_attributes = True


