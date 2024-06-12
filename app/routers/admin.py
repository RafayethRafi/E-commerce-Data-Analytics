from .. import models, schemas , oauth2,send_email
from fastapi import Response,status,HTTPException,Depends,APIRouter
from sqlalchemy.orm import Session
from ..database import get_db
from typing import List


router = APIRouter(
    prefix= "/admins",
    tags=['Admins']
)


@router.get("/admin-subscribe/{service_id}", status_code=status.HTTP_200_OK)
def subscribe_to_service(service_id:int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)) -> Response:
    

    if current_user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only Admins can subscribe to services")
    
    service = db.query(models.Services).filter(models.Services.id == service_id).first()

    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Service with id : {service_id} does not exist")
    
    subscription_query = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == service_id)
    
    found_subscription = subscription_query.first()

    if not found_subscription:
        new_subscription = models.SubscribedServices(organization_id = current_user.organization_id,service_id = service_id)
        db.add(new_subscription)
        db.commit()
        db.refresh(new_subscription)
        return f"Subscribed to {service.name} service"
    
    else:
        #already subscribed
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Already subscribed to {service.name} service")
    


@router.get("/admin-unsubscribe/{service_id}", status_code=status.HTTP_200_OK)
def unsubscribe_to_service(service_id:int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)) -> Response:
    

    if current_user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only Admins can unsubscribe to services")
    
    service = db.query(models.Services).filter(models.Services.id == service_id).first()

    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Service with id : {service_id} does not exist")
    
    subscription_query = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == service_id)
    
    found_subscription = subscription_query.first()

    if not found_subscription:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Not subscribed to {service.name} service")
    
    else:
        subscription_query.delete(synchronize_session=False)
        db.commit()
        return f"Unsubscribed from {service.name} service"
    



#an endpoint to find the users that are registered under an admin
@router.get("/registered_users/", status_code=status.HTTP_200_OK,response_model=List[schemas.UserOut])
def get_registered_users(db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)) -> Response:

    if current_user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only Admins can view registered users")
    
    registered_users = db.query(models.User).filter(models.User.organization_id == current_user.organization_id).all()

    if not registered_users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"No users registered under {current_user.email}")
    
    return registered_users



@router.post("/invite_users/", status_code=status.HTTP_200_OK)
async def invite_users(invitations : List[schemas.InvitationBase],db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)) -> Response:

    if current_user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only Admins can invite users")
    
    for invitation in invitations:
        new_invitation = models.Invitations(admin_id = current_user.admin_id,organization_id = current_user.organization_id,**invitation.model_dump())
        db.add(new_invitation)
        db.commit()
        db.refresh(new_invitation)

        send_email.send_invitation_email(invitation.email,invitation.role,current_user.admin_id)
        
    
    return f"Invited {len(invitations)} users"


# Find the emails that the admin invited but not registered yet
@router.get("/pending_invitations/", status_code=status.HTTP_200_OK,response_model=List[schemas.InvitationBase])
def get_pending_invitations(db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)) -> Response:

    if current_user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only Admins can view pending invitations")
    
    pending_invitations = db.query(models.Invitations).filter(models.Invitations.admin_id == current_user.admin_id,models.Invitations.is_registered == False).all()

    if not pending_invitations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"No pending invitations for {current_user.email}")
    
    return pending_invitations