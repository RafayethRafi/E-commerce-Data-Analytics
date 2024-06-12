from .. import models, schemas,oauth2
from fastapi import status,Depends,APIRouter
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(
    prefix = "/services",
    tags = ['Services']
)


@router.post("/",status_code=status.HTTP_201_CREATED,response_model=schemas.ServiceOut)
def create_service(service: schemas.ServiceCreate,db: Session = Depends(get_db)):

    new_service = models.Services(**service.model_dump())
    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    return new_service



