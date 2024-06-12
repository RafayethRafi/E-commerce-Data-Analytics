# from fastapi import Response,HTTPException,Depends
# from sqlalchemy.orm import Session
# from ...database import get_db
# from ... import oauth2
# from . import woocommerce_schemas,woocommerce_models
# from ..text_analysis.profanity_analysis import profanityAnalysis

# from celery import shared_task
# from app.Services_Router.Woocommerce_review_analysis.woocommerce_routers import get_reviews_and_store_in_db

# @shared_task
# def s_task():
#     db = Depends(get_db())
#     current_user = Depends(oauth2.get_current_user)
#     store_id = 2

#     get_reviews_and_store_in_db(store_id,db,current_user)
