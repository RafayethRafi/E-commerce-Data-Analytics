from pydantic import BaseModel,EmailStr,HttpUrl
from datetime import datetime


class Review(BaseModel):
    id: int
    product_id: int
    product_name: str
    reviewer: str
    reviewer_email: EmailStr
    review: str
    rating: int
    review_sentiment: float
    date_created : datetime

class ReviewOut(Review):
    store_id: int
    organization_id: int

    class Config:
        from_attributes = True


class WooUserCredentials(BaseModel):
    woocommerce_url : str
    consumer_key :str
    consumer_secret :str

class StoreOut(BaseModel):
    store_id: int

    class Config:
        from_attributes = True



class ReviewWebhookPayload(BaseModel):
    id: int
    product_id: int
    reviewer_name: str
    review_date: str
    rating: int
    review_text: str
