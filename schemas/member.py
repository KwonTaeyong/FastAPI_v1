from pydantic import BaseModel
from datetime import datetime

class MemberLogin(BaseModel):
    mb_id: str
    mb_pwd: str
    
class MemberCreate(BaseModel):
    mb_id: str
    mb_pwd: str

