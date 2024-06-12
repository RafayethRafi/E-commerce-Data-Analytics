from .database import Base
from sqlalchemy import Column,Integer,String,Boolean,TIMESTAMP,text,ForeignKey
from sqlalchemy .sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer,primary_key=True,nullable=False)
    name = Column(String,nullable=False)
    email = Column(String,nullable=False, unique=True)
    password = Column(String,nullable=False)
    phone_number = Column(String,nullable=False)
    address = Column(String,nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False,server_default=text('now()'))


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer,primary_key=True,nullable=False)
    name = Column(String,nullable=False)
    email = Column(String,nullable=False, unique=True)
    password = Column(String,nullable=False)
    phone_number = Column(String,nullable=False)
    address = Column(String,nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False,server_default=text('now()'))
    
    organization_id = Column(Integer,ForeignKey("organizations.id",ondelete="CASCADE"),nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer,primary_key=True,nullable=False)
    name = Column(String,nullable=False)
    email = Column(String,nullable=False, unique=True)
    password = Column(String,nullable=False)
    phone_number = Column(String)
    address = Column(String,nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False,server_default=text('now()'))
    
    
    admin_id = Column(Integer,ForeignKey("admins.id",ondelete="CASCADE"),nullable=False)
    is_admin = Column(Boolean,nullable=False,default=False)

    organization_id = Column(Integer,ForeignKey("organizations.id",ondelete="CASCADE"),nullable=False)
    
    
    
class Services(Base):
    __tablename__ = "services"

    id = Column(Integer,primary_key=True,nullable=False)
    name = Column(String,nullable=False)


class SubscribedServices(Base):
    __tablename__ = "subscribed_services"

    organization_id = Column(Integer,ForeignKey("admins.id",ondelete="CASCADE"),primary_key=True)
    service_id = Column(Integer,ForeignKey("services.id",ondelete="CASCADE"),primary_key=True)


class Invitations(Base):
    __tablename__ = "invitations"

    id = Column(Integer,primary_key=True,nullable=False)
    email = Column(String,nullable=False)
    role = Column(String,nullable=False)
    admin_id = Column(Integer,ForeignKey("admins.id",ondelete="CASCADE"),nullable=False)
    organization_id = Column(Integer,ForeignKey("organizations.id",ondelete="CASCADE"),nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False,server_default=text('now()'))
    is_registered = Column(Boolean,nullable=False,default=False)





