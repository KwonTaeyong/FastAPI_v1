from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import school
from schemas.school import SchoolOut

router = APIRouter(prefix="/api/school", tags=["School"])

@router.get("/", response_model=list[SchoolOut])
def search_school(keyword: str = Query(""), db: Session = Depends(get_db)):
    query = db.query(school.School)

    if keyword:
        query = query.filter(school.School.sch_name.contains(keyword))

    return query.limit(50).all()

