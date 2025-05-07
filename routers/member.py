from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.member import Member
from schemas.member import MemberLogin, MemberCreate
from starlette.status import HTTP_401_UNAUTHORIZED
from utils.security import hash_password, verify_password

router = APIRouter(prefix="/api", tags=["member"])

@router.post("/login")
def login(login_data: MemberLogin, db: Session = Depends(get_db)):
    user = db.query(Member).filter(Member.mb_id == login_data.mb_id).first()

    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 일치하지 않습니다."
        )

    # bcrypt 해싱된 비밀번호인지 확인
    is_hashed = user.mb_pwd.startswith("$2b$") or user.mb_pwd.startswith("$2a$")

    # 해싱된 경우 → verify_password 사용 / 아니면 평문 비교
    is_verified = verify_password(login_data.mb_pwd, user.mb_pwd) if is_hashed else login_data.mb_pwd == user.mb_pwd

    if not is_verified:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 일치하지 않습니다."
        )

    return {
        "mb_no": user.mb_no,
        "mb_id": user.mb_id,
        "insert_dt": user.insert_dt,
        "update_dt": user.update_dt,
    }
    
@router.post("/sign")
def create_user(payload: MemberCreate, db: Session = Depends(get_db)):
    # 중복 아이디 검사
    existing_user = db.query(Member).filter(Member.mb_id == payload.mb_id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

    # 비밀번호 해싱
    hashed_pwd = hash_password(payload.mb_pwd)

    new_user = Member(
        mb_id=payload.mb_id,
        mb_pwd=hashed_pwd
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "회원이 추가되었습니다.", "id": new_user.mb_id}