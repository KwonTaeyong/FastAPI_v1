from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.division import  Division
from schemas.division import DivisionCreate, DivisionOut, DivisionUpdate, DivisionDelete

router = APIRouter(prefix="/api", tags=["division"])

@router.post('/division/add')
def create_division(payload: DivisionCreate, db: Session = Depends(get_db)):
  
  new_division = Division(
      div_cd = payload.div_cd,
      div_name = payload.div_name,
      div_yn = payload.div_yn
  )
  db.add(new_division)
  db.commit()
  db.refresh(new_division)
  return {"message": "패키지가 추가되었습니다.", "div_name": new_division.div_name}


@router.get("/divisions", response_model=list[DivisionOut])
def get_divisions(db: Session = Depends(get_db)):
    return db.query(Division).all()
  
  
@router.put("/division/update")
def update_division(payload: DivisionUpdate, db: Session = Depends(get_db)):
    division = db.query(Division).filter(Division.div_cd == payload.div_cd).first()

    if not division:
        raise HTTPException(status_code=404, detail="해당 구분코드를 찾을 수 없습니다.")

    division.div_name = payload.div_name
    division.div_yn = payload.div_yn

    db.commit()
    db.refresh(division)

    return {"message": "패키지가 수정되었습니다.", "division": {
        "div_cd": division.div_cd,
        "div_name": division.div_name,
        "div_yn": division.div_yn
    }}
    
@router.delete("/division/delete/{div_cd}", status_code=200)
def delete_division(div_cd: int, db: Session = Depends(get_db)):
    division = db.query(Division).filter(Division.div_cd == div_cd).first()
    if not division:
        raise HTTPException(status_code=404, detail="해당 패키지를 찾을 수 없습니다.")
    
    db.delete(division)
    db.commit()
    return {"message": f"{div_cd}번 패키지 삭제 완료"}