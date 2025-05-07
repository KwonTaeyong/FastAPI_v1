from sqlalchemy.orm import Session
from models.container import Container

def get_all_containers(db: Session):
    return db.query(Container).all()
