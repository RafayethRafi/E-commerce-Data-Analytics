from ... import oauth2,models
from fastapi import HTTPException,Depends,APIRouter,status
from sqlalchemy.orm import Session
from ...database import get_db,cache
from typing import List
import requests
from . import e_commerce_schemas,e_commerce_models
from datetime import datetime
from .e_commerce_analysis_functions import reviewSentiment,reviewAnalysis
import json
from ..text_analysis.profanity_analysis import profanityAnalysis


router = APIRouter(
    prefix= "/Service-Woocommerce",
    tags=['Service-Woocommerce']
)

# cache = redis.Redis(host='localhost', port=6379)


# WooCommerce API credentials
    # woocommerce_url = "woo-wildly-psychic-otter.wpcomstaging.com/wp-json/wc/v3"
    # consumer_key = "ck_4b238f52b48610bfc29d009637f3bf4af9973fd9"
    # consumer_secret = "cs_b1bf9b99d32c8e5d6a5ab9760b7c73080abfe113"


#define a route to get the store api info and connect to the store
@router.post("/woocommerce-integration")
def get_user_credentials(user_credentials: e_commerce_schemas.WooUserCredentials, store_type:str ,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    
    #if not subscribed to the service raise exception
    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 5).first()

    if not subscribed_service:
        raise HTTPException(status_code=400,detail="You are not subscribed to this service")
    
    is_admin = db.query(models.User).filter(models.User.id == current_user.id).first().is_admin

    if is_admin == False:
        raise HTTPException(status_code=403,detail="Only admins can connect to the store")
    
    # check if the woocommerce_url has https:// in the beginning by strign index remove it
    if str(user_credentials.woocommerce_url)[:8] == "https://":
        user_credentials.woocommerce_url = str(user_credentials.woocommerce_url)[8:]

 
    woocommerce_url = f"https://{user_credentials.woocommerce_url}/wp-json/wc/v3"
    consumer_key = user_credentials.consumer_key
    consumer_secret = user_credentials.consumer_secret


    woocommerce_credentials = e_commerce_models.EcommerceIntegrations(organization_id = current_user.organization_id,site_url = woocommerce_url,wc_consumer_key = consumer_key,wc_consumer_secret = consumer_secret,store_type = store_type)

    #if credentials already exists in the database raise exception
    if db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id,e_commerce_models.EcommerceIntegrations.site_url == woocommerce_url,e_commerce_models.EcommerceIntegrations.wc_consumer_key == consumer_key,e_commerce_models.EcommerceIntegrations.wc_consumer_secret == consumer_secret).first():
        raise HTTPException(status_code=400,detail="You have already connected to this store")

    db.add(woocommerce_credentials)
    db.commit()
    db.refresh(woocommerce_credentials)

    return {"message":"Successfully connected to the store"}


#get store id's under an organization
@router.get("/store-ids")
def get_store_ids(db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    #if not subscribed to the service raise exception
    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 5).first()

    if not subscribed_service:
        raise HTTPException(status_code=400,detail="You are not subscribed to this service")
    
    #get the id's feild or column values of woocommerce_integrations table under an organization and make a list
    store_ids = db.query(e_commerce_models.EcommerceIntegrations.id).filter(e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id,e_commerce_models.EcommerceIntegrations.store_type=="woocommerce").all()
    
    #make a list of store_id's and store url's
    
    store_ids = [{"store_id":store_id[0],"site_url":db.query(e_commerce_models.EcommerceIntegrations.site_url).filter(e_commerce_models.EcommerceIntegrations.id == store_id[0]).first()[0][:-14]} for store_id in store_ids]
    return store_ids

    # return db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id).all()


def serialize_review(review):
    return {
        "id": review.id,
        "store_id": review.store_id,
        "product_id": review.product_id,
        "product_name": review.product_name,
        "reviewer_name": review.reviewer_name,
        "reviewer_email": review.reviewer_email,
        "review": review.review,
        "rating": review.rating,
        "review_sentiment": review.review_sentiment,
        "date_created": str(review.date_created),
        "organization_id": review.organization_id,
        "review_id": review.review_id,
        "verified": review.verified,
        "store_type": review.store_type
    }


async def get_reviews_and_store_in_db(store_id :int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    #get the store api info from the database by store id and organization id
    woocommerce_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id,e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id).first()

    #if credentials not found raise exception
    if not woocommerce_credentials:
        raise HTTPException(status_code=400,detail="You have not connected to the store yet")
    
    #if there are not any reviews in the database of the store by store_id then add all the reviews to the database
    if not db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.store_id == store_id,e_commerce_models.EcommerceReview.organization_id == current_user.organization_id).first():

        response = requests.get(
            f"{woocommerce_credentials.site_url}/products/reviews",
            auth=(woocommerce_credentials.wc_consumer_key, woocommerce_credentials.wc_consumer_secret)
        )
        
        if response.status_code == 200:
            reviews = response.json()
            
            if len(reviews) >0 :
                reviews_for_cache = []

                #add the reviews to the database
                for review in reviews:

                    #remove the html tags from the review
                    review["review"] = review["review"][3:-5]

                    #get the sentiment of the review
                    review["review_sentiment"] = reviewSentiment(review["review"])

                    review = e_commerce_models.EcommerceReview(store_id = store_id,product_id = review["product_id"],product_name = review["product_name"],reviewer_name = review["reviewer"],reviewer_email = review["reviewer_email"],review = review["review"],rating = review["rating"],date_created = datetime.strptime(review["date_created"],"%Y-%m-%dT%H:%M:%S"),organization_id = current_user.organization_id,review_sentiment = review["review_sentiment"],review_id = review["id"],verified = review["verified"],store_type = woocommerce_credentials.store_type)
                
                    db.add(review)
                    db.commit()
                    db.refresh(review)

                    reviews_for_cache.append(serialize_review(review))
            
                reviews_json = json.dumps(reviews_for_cache)

                cache.set(f"reviews_{store_id}",reviews_json,ex=3600)

        else:
            return {"error": "Failed to fetch reviews"}
        
    else:
        response = requests.get(
            f"{woocommerce_credentials.site_url}/products/reviews",
            params={"after": db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.organization_id == current_user.organization_id,e_commerce_models.EcommerceReview.store_id == store_id).order_by(e_commerce_models.EcommerceReview.date_created.desc()).first().date_created.strftime("%Y-%m-%dT%H:%M:%S")},
            auth=(woocommerce_credentials.wc_consumer_key, woocommerce_credentials.wc_consumer_secret)
        )

        #if no reviews are cached then get the reviews of that store from the database and cash the reviews
        if not cache.get(f"reviews_{store_id}"):
            reviews = db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.store_id == store_id,e_commerce_models.EcommerceReview.organization_id == current_user.organization_id).all()

            reviews_for_cache = []

            for review in reviews:
                reviews_for_cache.append(serialize_review(review))

            reviews_json = json.dumps(reviews_for_cache)

            cache.set(f"reviews_{store_id}",reviews_json,ex=3600)


        if response.status_code == 200:
            reviews = response.json()

            if len(reviews) >0:
                #get the reviews from the cache
                reviews_from_cache = json.loads(cache.get(f"reviews_{store_id}"))

            
                #add the reviews to the database
                for review in reviews:

                    #remove the html tags from the review
                    review["review"] = review["review"][3:-5]

                    #get the sentiment of the review
                    review["review_sentiment"] = reviewSentiment(review["review"])

                    review = e_commerce_models.EcommerceReview(store_id = store_id,product_id = review["product_id"],product_name = review["product_name"],reviewer_name = review["reviewer"],reviewer_email = review["reviewer_email"],review = review["review"],rating = review["rating"],date_created = datetime.strptime(review["date_created"],"%Y-%m-%dT%H:%M:%S"),organization_id = current_user.organization_id,review_sentiment = review["review_sentiment"],review_id = review["id"],verified = review["verified"],store_type = woocommerce_credentials.store_type)
                
                    db.add(review)
                    db.commit()
                    db.refresh(review)

                    reviews_from_cache.append(serialize_review(review))

                reviews_json = json.dumps(reviews_from_cache)
                #replace the old reviews with the new reviews in the cache
                cache.set(f"reviews_{store_id}",reviews_json,ex=3600)

                #return reviews
            
        else:
            return {"error": "Failed to fetch reviews"}
        

# Define a route to get store reviews
@router.get("/store-reviews/{store_id}",status_code=status.HTTP_200_OK)
async def get_store_reviews(store_id :int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    #if not subscribed to the service raise exception
    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 5).first()

    if not subscribed_service:
        raise HTTPException(status_code=400,detail="You are not subscribed to this service")

    await get_reviews_and_store_in_db(store_id,db,current_user)
    
    #get the reviews from the cache
    reviews = json.loads(cache.get(f"reviews_{store_id}"))


    analysis_val = reviewAnalysis(reviews)
    
    #return the overall sentiment of the store and the reviews
    return {"Overall Sentiment":analysis_val["sentiment"],"Positive reviews":f"{analysis_val['pos_per']}%","Negative reviews":f"{analysis_val['neg_per']}%","Neutral Reviews":f"{analysis_val['neu_per']}%","reviews":
            [{"product_id":review["product_id"],"product_name":review["product_name"],"review_id" : review["review_id"],review["review"] : "Positive" if review["review_sentiment"] >= 0.05 else "Negative" if review["review_sentiment"] <= -0.05 else "Neutral"} for review in reviews]
            }


async def get_store_reviews_for_dashboad(store_id :int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    #if not subscribed to the service raise exception
    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 5).first()

    if not subscribed_service:
        raise HTTPException(status_code=400,detail="You are not subscribed to this service")

    await get_reviews_and_store_in_db(store_id,db,current_user)
    
    #get the reviews from the cache
    reviews = json.loads(cache.get(f"reviews_{store_id}"))


    return reviews



    


@router.get("/product-reviews/{store_id}_{product_id}")
async def get_product_reviews(store_id:int,product_id: int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    #if not subscribed to the service raise exception
    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 5).first()

    if not subscribed_service:
        raise HTTPException(status_code=400,detail="You are not subscribed to this service")

    
    await get_reviews_and_store_in_db(store_id,db,current_user)

    #if the product id is not in the database then raise exception
    if not db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.product_id == product_id,e_commerce_models.EcommerceReview.organization_id == current_user.organization_id, e_commerce_models.EcommerceReview.store_id==store_id).first():
        raise HTTPException(status_code=400,detail="The product does not have any reviews")
    
    #get the reviews from the cache
    reviews = json.loads(cache.get(f"reviews_{store_id}"))

    #only get the reviews of the product
    reviews = [review for review in reviews if review["product_id"] == product_id]

    analysis_val = reviewAnalysis(reviews)
    
    #return the overall sentiment of the store and the reviews
    return {"Overall Sentiment":analysis_val["sentiment"],"Positive reviews":f"{analysis_val['pos_per']}%","Negative reviews":f"{analysis_val['neg_per']}%","Neutral Reviews":f"{analysis_val['neu_per']}%","reviews":
            [{"product_id : ":review["product_id"],"product_name":review["product_name"], "review_id":review["review_id"] ,review["review"] : "Positive" if review["review_sentiment"] >= 0.05 else "Negative" if review["review_sentiment"] <= -0.05 else "Neutral"} for review in reviews]
            }


@router.get("/profanity-reviews/{store_id}")
async def delete_review(store_id:int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    #if not subscribed to the service raise exception
    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 5).first()

    if not subscribed_service:
        raise HTTPException(status_code=400,detail="You are not subscribed to this service")

    await get_reviews_and_store_in_db(store_id,db,current_user)
    
    #get the reviews from the cache
    reviews = json.loads(cache.get(f"reviews_{store_id}"))

    #make a dictionary of the reviews which has the review id as the key and the review as the value
    reviews_dict = {review["review_id"]: {"review": review["review"], "product_id": review["product_id"],"product_name":review["product_name"]} for review in reviews}

    result = profanityAnalysis(reviews_dict)

    #get only the results which has the profanity_words not empty
    result = [item for item in result if len(item["profanity_words"]) > 0]

    return result


@router.delete("/delete-review/{store_id}_{review_id}")
async def delete_review(store_id:int,review_id:int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    #if not subscribed to the service raise exception
    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 5).first()

    if not subscribed_service:
        raise HTTPException(status_code=400,detail="You are not subscribed to this service")
    

    #get the store api info from the database by store id and organization id
    woocommerce_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id,e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id).first()

    #if credentials not found raise exception
    if not woocommerce_credentials:
        raise HTTPException(status_code=400,detail="You have not connected to the store yet")
    
    response = requests.delete(
        f"{woocommerce_credentials.site_url}/products/reviews/{review_id}",
        auth=(woocommerce_credentials.wc_consumer_key, woocommerce_credentials.wc_consumer_secret)
    )

    if response.status_code == 200:
        db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.review_id == review_id,e_commerce_models.EcommerceReview.organization_id == current_user.organization_id, e_commerce_models.EcommerceReview.store_id==store_id).delete()
        db.commit()

        #remove the key from the cache

        reviews = json.loads(cache.get(f"reviews_{store_id}"))

        reviews = [review for review in reviews if review["review_id"] != review_id]
        reviews_json = json.dumps(reviews)
        cache.set(f"reviews_{store_id}",reviews_json,ex=3600)


        return {"message":"Successfully deleted the review"}
    else:
        return {"error": "Failed to delete the review"}
    

@router.delete("/delete-bulk-reviews/{store_id}")
async def delete_bulk_reviews(store_id:int,review_ids: List[int],db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    #if not subscribed to the service raise exception
    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 5).first()

    if not subscribed_service:
        raise HTTPException(status_code=400,detail="You are not subscribed to this service")
    

    #get the store api info from the database by store id and organization id
    woocommerce_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id,e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id).first()

    #if credentials not found raise exception
    if not woocommerce_credentials:
        raise HTTPException(status_code=400,detail="You have not connected to the store yet")
    
    for review_id in review_ids:
        response = requests.delete(
            f"{woocommerce_credentials.site_url}/products/reviews/{review_id}",
            auth=(woocommerce_credentials.wc_consumer_key, woocommerce_credentials.wc_consumer_secret)
        )

        if response.status_code == 200:
            db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.review_id == review_id,e_commerce_models.EcommerceReview.organization_id == current_user.organization_id, e_commerce_models.EcommerceReview.store_id==store_id).delete()
            db.commit()
        else:
            return {"error": "Failed to delete the review"}
    
    #remove the key from the cache

    reviews = json.loads(cache.get(f"reviews_{store_id}"))

    reviews = [review for review in reviews if review["review_id"] not in review_ids]
    reviews_json = json.dumps(reviews)
    cache.set(f"reviews_{store_id}",reviews_json,ex=3600)

    
    return {"message":"Successfully deleted the reviews"}

@router.delete("/delete-all-cursed/{store_id}")
async def delete_all_cursed(store_id:int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    #if not subscribed to the service raise exception
    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 5).first()

    if not subscribed_service:
        raise HTTPException(status_code=400,detail="You are not subscribed to this service")
    

    #get the store api info from the database by store id and organization id
    woocommerce_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id,e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id).first()

    #if credentials not found raise exception
    if not woocommerce_credentials:
        raise HTTPException(status_code=400,detail="You have not connected to the store yet")
    
    #
    await get_reviews_and_store_in_db(store_id,db,current_user)
    
    #get all the reviews from the database
    reviews = db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.organization_id == current_user.organization_id,e_commerce_models.EcommerceReview.store_id == store_id).all()
    
    serialized_reviews = []
    for review in reviews:
        serialized_reviews.append(serialize_review(review))

    #make a dictionary of the reviews which has the review id as the key and the review as the value
    reviews_dict = {review["review_id"]: {"review": review["review"], "product_id": review["product_id"],"product_name":review["product_name"]} for review in serialized_reviews}

    result = profanityAnalysis(reviews_dict)

    #get only the results which has the profanity_words not empty
    result = [item for item in result if len(item["profanity_words"]) > 0]

    for item in result:
        response = requests.delete((f"{woocommerce_credentials.site_url}/products/reviews/{item['review_id']}"),auth=(woocommerce_credentials.wc_consumer_key, woocommerce_credentials.wc_consumer_secret))

        if response.status_code == 200:
            db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.review_id == item["review_id"],e_commerce_models.EcommerceReview.organization_id == current_user.organization_id, e_commerce_models.EcommerceReview.store_id==store_id).delete()
            db.commit()
        else:
            return {"error": "Failed to delete the review"}
    
    #remove the key from the cache

    reviews = json.loads(cache.get(f"reviews_{store_id}"))

    reviews = [review for review in reviews if review["review_id"] not in [item["review_id"] for item in result]]
    reviews_json = json.dumps(reviews)
    cache.set(f"reviews_{store_id}",reviews_json,ex=3600)
        
    return {"message":"Successfully deleted the reviews"}




@router.put("/change-delete-reviews-settings/{store_id}")
async def change_delete_reviews_settings(store_id:int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    #if not subscribed to the service raise exception
    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 5).first()

    if not subscribed_service:
        raise HTTPException(status_code=400,detail="You are not subscribed to this service")
    

    #get the store api info from the database by store id and organization id
    woocommerce_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id,e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id).first()

    #if credentials not found raise exception
    if not woocommerce_credentials:
        raise HTTPException(status_code=400,detail="You have not connected to the store yet")
    
    woocommerce_credentials.delete_cursed_words = not woocommerce_credentials.delete_cursed_words

    db.commit()

    return {"message":f"Successfully changed the delete reviews settings to {woocommerce_credentials.delete_cursed_words}"}


#get the products of the products in the store
@router.get("/products/{store_id}")
async def get_product(store_id:int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    woocommerce_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id,e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id).first()

    #if credentials not found raise exception
    if not woocommerce_credentials:
        raise HTTPException(status_code=400,detail="You have not connected to the store yet")
    
    response = requests.get(
        f"{woocommerce_credentials.site_url}/products",
        auth=(woocommerce_credentials.wc_consumer_key, woocommerce_credentials.wc_consumer_secret)
    )

    if response.status_code == 200:
        products = response.json()

        #make a list of the product id's and the product names
        products = [{"product_id":product["id"],"product_name":product["name"]} for product in products]
        return products
    else:
        return {"error": "Failed to fetch products"}



#define a route to get store orders
@router.get("/store-orders/{store_id}")
async def get_store_orders(store_id:int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    # Make a GET request to the WooCommerce API to fetch orders

    woocommerce_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id,e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id).first()


    if not woocommerce_credentials:
        raise HTTPException(status_code=400,detail="You have not connected to the store yet")

    #if there are not any orders in the database then add all the orders to the database
    if not db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id,e_commerce_models.EcommerceOrder.store_id == store_id).first():
        response = requests.get(
            f"{woocommerce_credentials.site_url}/orders",
            auth=(woocommerce_credentials.wc_consumer_key, woocommerce_credentials.wc_consumer_secret)
        )

        if response.status_code == 200:
            orders = response.json()

            #add the orders to the database
            for order in orders:
                total = float(order["total"])
                order = e_commerce_models.EcommerceOrder(store_id = store_id,order_id = order["id"],financial_status = order["status"],date_created = datetime.strptime(order["date_created"],"%Y-%m-%dT%H:%M:%S"),date_modified = datetime.strptime(order["date_modified"],"%Y-%m-%dT%H:%M:%S"),total = total,first_name = order["billing"]["first_name"],last_name = order["billing"]["last_name"],address_1 = order["billing"]["address_1"],address_2 = order["billing"]["address_2"],city = order["billing"]["city"],state = order["billing"]["state"],postcode = order["billing"]["postcode"],country = order["billing"]["country"],email = order["billing"]["email"],phone = order["billing"]["phone"],payment_method = order["payment_method"],customer_note = order["customer_note"],line_items = [item["product_id"] for item in order["line_items"]],quantity = [item["quantity"] for item in order["line_items"]],organization_id = current_user.organization_id,prices = [item["price"] for item in order["line_items"]],sku = [item["sku"] for item in order["line_items"]],store_type = woocommerce_credentials.store_type,currency = order["currency"],ip_address = order["customer_ip_address"],customer_id = order["customer_id"])
                db.add(order)
                db.commit()
                db.refresh(order)
            return orders
        else:
            return {"error": "Failed to fetch orders"}
        
    else:
        # get the new orders and add the modified orders and add the new orders to database and update the modified orders on database
        response = requests.get(
            f"{woocommerce_credentials.site_url}/orders",
            params={"after": db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id,e_commerce_models.EcommerceOrder.store_id == store_id).order_by(e_commerce_models.EcommerceOrder.date_created.desc()).first().date_created.strftime("%Y-%m-%dT%H:%M:%S")},
            auth=(woocommerce_credentials.wc_consumer_key, woocommerce_credentials.wc_consumer_secret)
        )

        if response.status_code == 200:
            orders = response.json()

            #add the orders to the database
            for order in orders:
                total = float(order["total"])
                order = e_commerce_models.EcommerceOrder(store_id = store_id,order_id = order["id"],financial_status = order["status"],date_created = datetime.strptime(order["date_created"],"%Y-%m-%dT%H:%M:%S"),date_modified = datetime.strptime(order["date_modified"],"%Y-%m-%dT%H:%M:%S"),total = total,first_name = order["billing"]["first_name"],last_name = order["billing"]["last_name"],address_1 = order["billing"]["address_1"],address_2 = order["billing"]["address_2"],city = order["billing"]["city"],state = order["billing"]["state"],postcode = order["billing"]["postcode"],country = order["billing"]["country"],email = order["billing"]["email"],phone = order["billing"]["phone"],payment_method = order["payment_method"],customer_note = order["customer_note"],line_items = [item["product_id"] for item in order["line_items"]],quantity = [item["quantity"] for item in order["line_items"]],organization_id = current_user.organization_id,prices = [item["price"] for item in order["line_items"]],sku = [item["sku"] for item in order["line_items"]],store_type = woocommerce_credentials.store_type,currency = order["currency"],ip_address = order["customer_ip_address"],customer_id = order["customer_id"])
                db.add(order)
                db.commit()
                db.refresh(order)
        
        else:
            return {"error": "Failed to fetch orders"}
        
        #update the modified orders in the database
        response = requests.get(
            f"{woocommerce_credentials.site_url}/orders",
            params={"after": db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id,e_commerce_models.EcommerceOrder.store_id == store_id).order_by(e_commerce_models.EcommerceOrder.date_modified.desc()).first().date_modified.strftime("%Y-%m-%dT%H:%M:%S")},
            auth=(woocommerce_credentials.wc_consumer_key, woocommerce_credentials.wc_consumer_secret)
        )

        if response.status_code == 200:
            orders = response.json()

            #update the modified orders in the database
            for order in orders:
                total = float(order["total"])
                db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.order_id == order["id"],e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id,e_commerce_models.EcommerceOrder.store_id == store_id).update({"financial_status":order["status"],"date_modified":datetime.strptime(order["date_modified"],"%Y-%m-%dT%H:%M:%S"),"total":total,"first_name":order["billing"]["first_name"],"last_name":order["billing"]["last_name"],"address_1":order["billing"]["address_1"],"address_2":order["billing"]["address_2"],"city":order["billing"]["city"],"state":order["billing"]["state"],"postcode":order["billing"]["postcode"],"country":order["billing"]["country"],"email":order["billing"]["email"],"phone":order["billing"]["phone"],"payment_method":order["payment_method"],"customer_note":order["customer_note"],"line_items":[item["product_id"] for item in order["line_items"]],"quantity":[item["quantity"] for item in order["line_items"]],"prices":[item["price"] for item in order["line_items"]],"sku":[item["sku"] for item in order["line_items"]],"currency":order["currency"],"ip_address":order["customer_ip_address"],"customer_id":order["customer_id"]})
                db.commit()
            
        
        return db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id,e_commerce_models.EcommerceOrder.store_id==store_id).all()
    

        
    


#define a route to get the customers
# @router.get("/customers")
# async def get_customers(db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
#     # Make a GET request to the WooCommerce API to fetch customers

#     woocommerce_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id).first()


#     if not woocommerce_credentials:
#         raise HTTPException(status_code=400,detail="You have not connected to the store yet")

#     response = requests.get(
#         f"{woocommerce_credentials.site_url}/customers",
#         auth=(woocommerce_credentials.wc_consumer_key, woocommerce_credentials.wc_consumer_secret)
#     )

#     if response.status_code == 200:
#         customers = response.json()
#         return customers
#     else:
#         return {"error": "Failed to fetch customers"}
    


# get the orders from the store
# @router.get("/orders/{store_id}")
# async def get_orders(store_id:int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
#     # Make a GET request to the WooCommerce API to fetch orders

#     woocommerce_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id,e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id).first()


#     if not woocommerce_credentials:
#         raise HTTPException(status_code=400,detail="You have not connected to the store yet")

#     #get all the orders from the store
#     response = requests.get(
#         f"{woocommerce_credentials.site_url}/orders",
#         auth=(woocommerce_credentials.wc_consumer_key, woocommerce_credentials.wc_consumer_secret)
#     )

#     if response.status_code == 200:
#         orders = response.json()
#         return orders
#     else:
#         return {"error": "Failed to fetch orders"}