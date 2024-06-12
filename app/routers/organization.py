from .. import models, schemas , utils,oauth2
from fastapi import status,HTTPException,Depends,APIRouter
from sqlalchemy.orm import Session
from ..database import get_db
from typing import List


router = APIRouter(
    prefix= "/organization",
    tags=['Organization']
)

@router.post("/register/",status_code=status.HTTP_201_CREATED,response_model=schemas.UserOut)
def create_organization(org:schemas.OrganizationCreate, db: Session = Depends(get_db)):


    #if organization already exists by email
    if db.query(models.Organization).filter(models.Organization.email == org.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Organization already exists")


    hashed_password = utils.hash(org.password)
    org.password = hashed_password

    new_org = models.Organization(**org.model_dump())
    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    
    new_admin = models.Admin(organization_id = new_org.id,**org.model_dump())
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    new_admin_user = models.User(admin_id = new_admin.id,organization_id = new_org.id,is_admin=True,**org.model_dump())
    db.add(new_admin_user)
    db.commit()
    db.refresh(new_admin_user)

    return new_admin_user



#find all members of an organization
@router.get("/organization-members/",status_code=status.HTTP_200_OK,response_model=List[schemas.UserOut])
def get_organization_members(db: Session = Depends(get_db),current_user:int = Depends(oauth2.get_current_user)):
    if current_user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only Admins can view members")
    
    members = db.query(models.User).filter(models.User.organization_id == current_user.organization_id).all()

    return members