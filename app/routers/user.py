from .. import models, schemas , utils,oauth2,send_email
from fastapi import Response,status,HTTPException,Depends,APIRouter
from sqlalchemy.orm import Session
from ..database import get_db
from typing import List

router = APIRouter(
    prefix= "/users",
    tags=['Users']
)

@router.post("/register_user/{email}_{role}_{admin_id}",status_code=status.HTTP_201_CREATED,response_model=schemas.UserOut)
def create_user(email:str,role:str,admin_id:int,user:schemas.UserCreate, db: Session = Depends(get_db)):

    hashed_password = utils.hash(user.password)
    user.password = hashed_password

    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"{email} already registered")
    
    invitation_query =  db.query(models.Invitations).filter(models.Invitations.email == email).first()
    if not invitation_query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"{email} not invited")

    organization_id = db.query(models.Admin).filter(models.Admin.id == admin_id).first().organization_id

    if role == "admin":
        new_admin = models.Admin(organization_id = organization_id,**user.model_dump())

        if new_admin.email != email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Email does not match")
        
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)


    if role == "admin": 
        new_user = models.User(is_admin=True,admin_id = new_admin.id,organization_id= organization_id,**user.model_dump())
    else:
       new_user = models.User(is_admin=False,admin_id = admin_id,organization_id= organization_id,**user.model_dump()) 

    if(new_user.email != email):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Email does not match")
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    #update invitation is_registered to True
    invitation_query.is_registered = True
    db.commit()
    db.refresh(invitation_query)

    return new_user


@router.get("/subscribed_services/", status_code=status.HTTP_200_OK,response_model=List[schemas.ServiceOut])
def get_subscribed_services(db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)) -> Response:

    subscribed_services = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id).all()

    #get service ids and service names
    subscribed_services = [{"id":service.service_id,"name":db.query(models.Services).filter(models.Services.id == service.service_id).first().name} for service in subscribed_services]

    if not subscribed_services:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"No services subscribed by {current_user.email}")

    return subscribed_services


#an endpoint to find the services that are not subscribed
@router.get("/unsubscribed_services/", status_code=status.HTTP_200_OK,response_model=List[schemas.ServiceOut])
def get_unsubscribed_services(db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)) -> Response:

    subscribed_services = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id).all()

    #get service ids and service names
    subscribed_services = [service.service_id for service in subscribed_services]

    all_services = db.query(models.Services).all()

    unsubscribed_services = [service for service in all_services if service.id not in subscribed_services]

    if not unsubscribed_services:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"All services were subscribed.")

    return unsubscribed_services


#forgot password and recovery
@router.post("/forgot_password/", status_code=status.HTTP_200_OK)
def forgot_password(data:schemas.ForgotPassword,db: Session = Depends(get_db)) -> Response:

    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"{data.email} not registered")

    send_email.send_pass_recovery_email(user.id,data.email)

    return f"Recovery email sent to {data.email} of id : {user.id}"