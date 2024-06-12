from pydantic import BaseModel,EmailStr
from datetime import datetime
from typing import Optional




# class AdminBase(BaseModel):
#     name : str
#     email : EmailStr
#     phone_number : str
#     address : str

class OrganizationBase(BaseModel):
    name : str
    email : EmailStr
    phone_number : str
    address : str

class OrganizationCreate(OrganizationBase):
    password: str

class OrganizationOut(OrganizationBase):
    pass



class InvitationBase(BaseModel):
    email : EmailStr
    role : str

class InvitationCreate(InvitationBase):
    admin_id : int
    organization_id : int
    

class AdminLogin(BaseModel):
    email : EmailStr
    password : str



class UserBase(BaseModel):
    name : str
    email : EmailStr
    phone_number : str
    address : str


class UserCreate(UserBase):
    password: str



class UserOut(UserBase):
    id: int
    created_at : datetime
    admin_id : int
    is_admin : bool
    organization_id : int

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email : EmailStr
    password : str



class ServiceBase(BaseModel):
    name : str


class ServiceCreate(ServiceBase):
    pass

class ServiceOut(ServiceBase):
    id : int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type : str


class TokenData(BaseModel):
    id : Optional[int] = None



class ForgotPassword(BaseModel):
    email : EmailStr


class PassReset(BaseModel):
    password : str