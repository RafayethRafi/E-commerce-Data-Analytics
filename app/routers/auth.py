from fastapi import APIRouter,Depends,status,HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import database , schemas,models,utils,oauth2
from app.Services_Router.Ecommerce_analysis.woocommerce_routers import get_reviews_and_store_in_db


router = APIRouter(tags=['Authentication'])

@router.post('/login',response_model=schemas.Token)
async def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    #user_credentials will return only usename and password
    
    # user = db.query(models.User).filter(models.User.email == user_credentials.email).first()

    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    if not utils.verify(user_credentials.password,user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials") 

    access_token = oauth2.create_access_token(data = {"user_id" : user.id})


    return {"access_token" : access_token, "token_type":"bearer"}



@router.put('/password_reset/{id}_{email}',status_code=status.HTTP_200_OK)
def password_reset(id:int,email:str,password:schemas.PassReset,db: Session = Depends(database.get_db)):
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user.id != id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    hashed_password = utils.hash(**password.model_dump())
    user.password = hashed_password
    db.commit()
    db.refresh(user)

    if user.is_admin:
        admin = db.query(models.Admin).filter(models.Admin.id == user.admin_id).first()
        admin.password = hashed_password
        db.commit()
        db.refresh(admin)

    return {"detail":"Password updated successfully"}
