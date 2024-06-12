from ...database import Base
from sqlalchemy import Column,Integer,String,TIMESTAMP,text,ForeignKey,ARRAY,Float,Boolean,BigInteger
from sqlalchemy .sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP



class EcommerceIntegrations(Base):
    __tablename__ = "e_commerce_integrations"

    id = Column(Integer,primary_key=True,nullable=False)
    organization_id = Column(Integer,ForeignKey("organizations.id",ondelete="CASCADE"),nullable=False)
    site_url = Column(String,nullable=False)
    wc_consumer_key = Column(String,nullable=True)
    wc_consumer_secret = Column(String,nullable=True)
    delete_cursed_words = Column(Boolean,nullable=False,default=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False,server_default=text('now()'))
    
    s_private_token = Column(String,nullable=True)
    s_judgeme_api_token = Column(String,nullable=True)

    store_type = Column(String,nullable=False,default="na")
    


class EcommerceReview(Base):
    __tablename__ = "e_commerce_reviews"

    id = Column(Integer,primary_key=True,nullable=False)
    review_id = Column(Integer,nullable=False)
    verified = Column(Boolean,nullable=True,default=False)
    store_id = Column(Integer,ForeignKey("e_commerce_integrations.id",ondelete="CASCADE"),nullable=False)
    product_id = Column(Integer,nullable=False)
    product_name = Column(String,nullable=False)
    reviewer_name = Column(String,nullable=True)
    reviewer_email = Column(String,nullable=True)
    review = Column(String,nullable=False)
    rating = Column(Integer,nullable=False)
    review_sentiment = Column(Float,nullable=False,default=0.0)
    date_created = Column(TIMESTAMP(timezone=False),nullable=False)
    date_updated = Column(TIMESTAMP(timezone=False),nullable=True)
    hidden = Column(Boolean,nullable=True,default=False)
    s_verified = Column(String,nullable=True,default=False)
    organization_id = Column(Integer,ForeignKey("organizations.id",ondelete="CASCADE"),nullable=False)

    store_type = Column(String,nullable=False,default="na")


class EcommerceOrder(Base):
    __tablename__ = "e_commerce_orders"

    id = Column(Integer,primary_key=True,nullable=False)
    store_id = Column(Integer,ForeignKey("e_commerce_integrations.id",ondelete="CASCADE"),nullable=False)
    order_id = Column(BigInteger,nullable=False)
    financial_status = Column(String,nullable=True)
    date_created = Column(TIMESTAMP(timezone=False),nullable=False)
    date_modified = Column(TIMESTAMP(timezone=False),nullable=True)
    total = Column(Float,nullable=False)
    prices = Column(ARRAY(Float),nullable=False,default=[])
    first_name = Column(String,nullable=True)
    last_name = Column(String,nullable=True)
    address_1 = Column(String,nullable=True)
    address_2 = Column(String,nullable=True)
    city = Column(String,nullable=True)
    state = Column(String,nullable=True)
    postcode = Column(String,nullable=True)
    country = Column(String,nullable=True)
    email = Column(String,nullable=True)
    phone = Column(String,nullable=True)
    payment_method = Column(String,nullable=True)
    customer_note = Column(String,nullable=True)
    line_items = Column(ARRAY(BigInteger),nullable=False)
    #add sku column and the default value should be empty array with string type
    sku = Column(ARRAY(String),nullable=False,default=[])
    quantity = Column(ARRAY(Integer),nullable=False)
    organization_id = Column(Integer,ForeignKey("organizations.id",ondelete="CASCADE"),nullable=False)

    store_type = Column(String,nullable=False,default="na")

    s_cancelled_at = Column(TIMESTAMP(timezone=False),nullable=True)
    s_cancel_reason = Column(String,nullable=True)

    currency = Column(String,nullable=True)
    s_fulfillment_status = Column(String,nullable=True)
    ip_address = Column(String,nullable=True,default="")
    customer_id = Column(BigInteger,nullable=True,default=0)



