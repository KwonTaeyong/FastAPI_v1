from pydantic import BaseModel
from typing import List, Optional

class ContainerOut(BaseModel):
    container_cd: int   
    sch_cd: int
    sch_name: str
    sch_nickname: Optional[str] = None
    domain: str
    grop_cd: int
    div_cd: int
    div_name: Optional[str] = None

    class Config:
        from_attributes = True

class ContainerUpdate(BaseModel):
    sch_name: str
    sch_nickname: Optional[str] = None
    domain: str
    grop_cd: int
    div_cd: int

class ContainerCreateItem(BaseModel):
    domain: str
    alias: Optional[str] = None
    div_cd: int

class ContainerCreate(BaseModel):
    sch_cd: int
    sch_name: str
    sch_nickname: Optional[str] = None
    grop_cd: int
    containers: List[ContainerCreateItem] 