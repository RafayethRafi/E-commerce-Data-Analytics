from ... import oauth2,models
from fastapi import HTTPException,Depends,APIRouter,status,Request
from sqlalchemy.orm import Session
from ...database import get_db,cache
import requests
from . import e_commerce_models
from .e_commerce_analysis_functions import reviewSentiment,reviewAnalysis
import json
from ..text_analysis.profanity_analysis import profanityAnalysis
from .import shopify_schemas


router = APIRouter(
    prefix= "/Service-Shopify",
    tags=['Service-Shopify']
)




#get store id's under an organization
@router.get("/store-ids")
def get_store_ids(db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    #if not subscribed to the service raise exception
    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 6).first()

    if not subscribed_service:
        raise HTTPException(status_code=400,detail="You are not subscribed to this service")
    
    #get the id's feild or column values of woocommerce_integrations table under an organization and make a list
    store_ids = db.query(e_commerce_models.EcommerceIntegrations.id).filter(e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id,e_commerce_models.EcommerceIntegrations.store_type=="shopify").all()
    
    #make a list of store_id's and store url's
    
    store_ids = [{"store_id":store_id[0],"site_url":db.query(e_commerce_models.EcommerceIntegrations.site_url).filter(e_commerce_models.EcommerceIntegrations.id == store_id[0]).first()[0]} for store_id in store_ids]
    return store_ids


#get a single shopify store product by it's id
@router.get('/shopify_products/{store_id}')
async def get_shopify_products(store_id:int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    shopify_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id,e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id,e_commerce_models.EcommerceIntegrations.store_type == "shopify").first()



    if not shopify_credentials:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="You have not connected to the store yet")
    
    product_list = []
    products = []
    id = "0"

    while True:
        endpoint = f"https://{shopify_credentials.site_url}/admin/api/2023-10/products.json?since_id={id}"
         
        headers = { "X-Shopify-Access-Token": shopify_credentials.s_private_token }

        response = requests.get(endpoint,headers=headers)

        if response.status_code == 200:
            products = response.json()

        if products["products"] == []:
            break

        for product in products["products"]:
            product_list.append({"product_id":product["id"],"product_name":product["title"]})
            id = product["id"]
        

    if product_list == []:
        return {"error": "Failed to get product"}
    
    return product_list



#get the stores info
@router.get('/shopify_store_info/{store_id}')
def get_shopify_store_info(store_id:int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    shopify_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id,e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id,e_commerce_models.EcommerceIntegrations.store_type == "shopify").first()

    if not shopify_credentials:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="You have not connected to the store yet")

    endpoint = f"https://{shopify_credentials.site_url}/admin/api/2023-10/shop.json"

    headers = {
        "X-Shopify-Access-Token": shopify_credentials.s_private_token,
    }

    response = requests.get(endpoint,headers=headers)

    if response.status_code == 200:
        store_info = response.json()
        return store_info
    else:
        return {"error": "Failed to get store info"}
    
    



#define a route to get the shopify store api info and connect to the store
@router.post('/shopify-integration')
def shopify_integration(user_credentials: shopify_schemas.ShopifyCredentials,db:Session = Depends(get_db),current_user:models.User = Depends(oauth2.get_current_user)):

    #if not subscribed to the service then raise exception

    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 6).first()

    if not subscribed_service:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You are not subscribed to this service")
    
    
    is_admin = db.query(models.User).filter(models.User.id == current_user.id).first().is_admin

    if is_admin == False:
        raise HTTPException(status_code=403,detail="Only admins can connect to the store")
    
    if str(user_credentials.shopify_url)[:8] == "https://":
        user_credentials.shopify_url = str(user_credentials.shopify_url)[8:]

    site_url = user_credentials.shopify_url
    s_private_token = user_credentials.s_private_token
    s_judgeme_api_token = user_credentials.s_judgeme_api_token



    shopify_credentials = e_commerce_models.EcommerceIntegrations(organization_id=current_user.organization_id,site_url=site_url,s_private_token=s_private_token,s_judgeme_api_token=s_judgeme_api_token,store_type = "shopify")

    #if credentials already exist then raise exception
    if db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id,e_commerce_models.EcommerceIntegrations.site_url==site_url,e_commerce_models.EcommerceIntegrations.s_private_token==s_private_token,s_judgeme_api_token==s_judgeme_api_token,e_commerce_models.EcommerceIntegrations.store_type == "shopify").first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You have already connected to a store")
    
    db.add(shopify_credentials)
    db.commit()
    db.refresh(shopify_credentials)

    return {"detail":"Store connected successfully"}
    
    

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
        "date_updated": str(review.date_updated),
        "organization_id": review.organization_id,
        "review_id": review.review_id,
        "s_verified": review.s_verified,
        "store_type": review.store_type
    }



async def get_reviews_and_store_in_db(store_id :int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    #get the store api info from the database by store id and organization id
    shopify_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id,e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id,e_commerce_models.EcommerceIntegrations.store_type == "shopify").first()

    if not shopify_credentials:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="You have not connected to the store yet")
    
    #if there are not any reviews in the database of the store by store_id then add all the reviews to the database

    if not db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.store_id == store_id,e_commerce_models.EcommerceReview.organization_id == current_user.organization_id,e_commerce_models.EcommerceReview.store_type == "shopify").first():
            
        #get the reviews of the store by using Judge.me API
        endpoint = f"https://judge.me/api/v1/reviews"
    
        reviews = []
        page = 1
        limit = 10
            
        headers = { "accept": "application/json" }
        
        while True:
            params = { "api_token": shopify_credentials.s_judgeme_api_token, "shop_domain": shopify_credentials.site_url, "page": page, "limit": limit}
            
            response = requests.get(endpoint,params=params,headers=headers)
    
            if response.status_code != 200:
                return {"detail":"Failed to get reviews"}
    
            x = response.json()
    
            if x["reviews"] == []:
                break
    
            for review in x["reviews"]:
                reviews.append(review)
    
            page += 1
    
        #add the reviews to the database

        if reviews == []:
            return {"detail":"No reviews found"}
        
        reviews_for_cache = []

        for review in reviews:

            review_sentiment = reviewSentiment(review["title"])

            review_to_add = e_commerce_models.EcommerceReview(
                store_id = store_id,
                product_id = review["product_external_id"],
                product_name = review["product_title"],
                reviewer_name = review["reviewer"]["name"],
                reviewer_email = review["reviewer"]["email"],
                review = review["title"],
                rating = review["rating"],
                date_created = review["created_at"],
                date_updated = review["updated_at"],
                organization_id = current_user.organization_id,
                review_sentiment = review_sentiment,
                review_id = review["id"],
                s_verified = review["verified"],
                store_type = "shopify"
            )
    
            db.add(review_to_add)
            db.commit()
            db.refresh(review_to_add)

            reviews_for_cache.append(serialize_review(review_to_add))

        reviews_json = json.dumps(reviews_for_cache)

        cache.set(f"reviews_{store_id}",reviews_json,ex=3600)
    
    else:

        #get the reviews of the store after the last time the reviews were added to the database according to the date_created column
        endpoint = f"https://judge.me/api/v1/reviews"
    
        reviews = []
        page = 1
        limit = 10
            
        headers = { "accept": "application/json" }
        
        if not cache.get(f"reviews_{store_id}"):
            reviews_c = db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.organization_id==current_user.organization_id,e_commerce_models.EcommerceReview.store_id==store_id).all()

            reviews_for_cache = []

            for review in reviews_c:
                reviews_for_cache.append(serialize_review(review))

            reviews_json = json.dumps(reviews_for_cache)

            cache.set(f"reviews_{store_id}",reviews_json,ex=3600)

        reviews_for_cache = json.loads(cache.get(f"reviews_{store_id}"))

        last_date_in_db_created = db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.organization_id==current_user.organization_id,e_commerce_models.EcommerceReview.store_id==store_id).order_by(e_commerce_models.EcommerceReview.date_created.desc()).first().date_created.strftime("%Y-%m-%dT%H:%M:%S")

        last_date_in_db_updated = db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.organization_id==current_user.organization_id,e_commerce_models.EcommerceReview.store_id==store_id).order_by(e_commerce_models.EcommerceReview.date_updated.desc()).first().date_updated.strftime("%Y-%m-%dT%H:%M:%S")

        last_date = max(last_date_in_db_created,last_date_in_db_updated)

        while True:
            params = {"api_token": shopify_credentials.s_judgeme_api_token, "shop_domain": shopify_credentials.site_url, "page": page, "limit": limit}
            
            response = requests.get(endpoint,params=params,headers=headers)
    
            if response.status_code != 200:
                return {"detail":"Failed to get reviews"}
            
    
            x = response.json()
    
            if x["reviews"] == []:
                break

            for review in x["reviews"]:
                reviews.append(review)
    
            page += 1
    
        #add the reviews to the database

        if reviews == []:
            return {"detail":"No reviews found"}

        #get the reviews created after the last date in db
        reviews = list(filter(lambda review: review["created_at"] > last_date, reviews))

        reviews_for_update = list(filter(lambda review: review["updated_at"] > last_date, reviews))

        for review in reviews:

            #if review already exists in the database then skip
            if db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.organization_id == current_user.organization_id,e_commerce_models.EcommerceReview.store_id == store_id,e_commerce_models.EcommerceReview.review_id == review["id"]).first():
                continue
            
            review_sentiment = reviewSentiment(review["title"])

            review_to_add = e_commerce_models.EcommerceReview(
                store_id = store_id,
                product_id = review["product_external_id"],
                product_name = review["product_title"],
                reviewer_name = review["reviewer"]["name"],
                reviewer_email = review["reviewer"]["email"],
                review = review["title"],
                rating = review["rating"],
                date_created = review["created_at"],
                date_updated = review["updated_at"],
                organization_id = current_user.organization_id,
                review_sentiment = review_sentiment,
                review_id = review["id"],
                s_verified = review["verified"],
                store_type = "shopify"
            )
    
            db.add(review_to_add)
            db.commit()
            db.refresh(review_to_add)

            reviews_for_cache.append(serialize_review(review_to_add))
        
        for review in reviews_for_update:
                
            review_sentiment = reviewSentiment(review["title"])
    
            review_to_update = db.query(e_commerce_models.EcommerceReview).filter(e_commerce_models.EcommerceReview.organization_id == current_user.organization_id,e_commerce_models.EcommerceReview.store_id == store_id,e_commerce_models.EcommerceReview.review_id == review["id"]).first()
    
            review_to_update.product_id = review["product_external_id"]
            review_to_update.product_name = review["product_title"]
            review_to_update.reviewer_name = review["reviewer"]["name"]
            review_to_update.reviewer_email = review["reviewer"]["email"]
            review_to_update.review = review["title"]
            review_to_update.rating = review["rating"]
            review_to_update.date_created = review["created_at"]
            review_to_update.date_updated = review["updated_at"]
            review_to_update.organization_id = current_user.organization_id
            review_to_update.review_sentiment = review_sentiment
            review_to_update.review_id = review["id"]
            review_to_update.s_verified = review["verified"]
            review_to_update.store_type = "shopify"
        
            db.commit()
            db.refresh(review_to_update)
    
            reviews_for_cache.append(serialize_review(review_to_update))

        reviews_json = json.dumps(reviews_for_cache)

        cache.set(f"reviews_{store_id}",reviews_json,ex=3600)



# Define a route to get store reviews
@router.get('/shopify_store-reviews/{store_id}',status_code=status.HTTP_200_OK)
async def get_store_reviews(store_id:int,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    #if not subscribed to the service then raise exception

    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 6).first()

    if not subscribed_service:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You are not subscribed to this service")
    
    await get_reviews_and_store_in_db(store_id,db,current_user)

    #get the reviews from the cache
    reviews = json.loads(cache.get(f"reviews_{store_id}"))

    analysis_val = reviewAnalysis(reviews)

        #return the overall sentiment of the store and the reviews
    return {"Overall Sentiment":analysis_val["sentiment"],"Positive reviews":f"{analysis_val['pos_per']}%","Negative reviews":f"{analysis_val['neg_per']}%","Neutral Reviews":f"{analysis_val['neu_per']}%","reviews":
            [{"product_id":review["product_id"],"product_name":review["product_name"],"review_id" : review["review_id"],review["review"] : "Positive" if review["review_sentiment"] >= 0.05 else "Negative" if review["review_sentiment"] <= -0.05 else "Neutral"} for review in reviews]
            }


@router.get("/shopify_product_reviews/{store_id}_{product_id}",status_code=status.HTTP_200_OK)
async def get_product_reviews(store_id:int,product_id: int,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    #if not subscribed to the service then raise exception

    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 6).first()

    if not subscribed_service:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You are not subscribed to this service")
    
    await get_reviews_and_store_in_db(store_id,db,current_user)

    #get the reviews from the cache
    reviews = json.loads(cache.get(f"reviews_{store_id}"))

    reviews = [review for review in reviews if review["product_id"] == product_id]

    analysis_val = reviewAnalysis(reviews)

        #return the overall sentiment of the store and the reviews
    return {"Overall Sentiment":analysis_val["sentiment"],"Positive reviews":f"{analysis_val['pos_per']}%","Negative reviews":f"{analysis_val['neg_per']}%","Neutral Reviews":f"{analysis_val['neu_per']}%","reviews":
            [{"product_id":review["product_id"],"product_name":review["product_name"],"review_id" : review["review_id"],review["review"] : "Positive" if review["review_sentiment"] >= 0.05 else "Negative" if review["review_sentiment"] <= -0.05 else "Neutral"} for review in reviews]
            }



async def get_store_reviews_for_dashboard(store_id:int,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    #if not subscribed to the service then raise exception

    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 6).first()

    if not subscribed_service:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You are not subscribed to this service")
    
    await get_reviews_and_store_in_db(store_id,db,current_user)

    #get the reviews from the cache
    reviews = json.loads(cache.get(f"reviews_{store_id}"))

    return reviews




@router.get("/profanity-reviews/{store_id}")
async def profanity_reviews(store_id:int,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    #if not subscribed to the service raise exception
    subscribed_service = db.query(models.SubscribedServices).filter(models.SubscribedServices.organization_id == current_user.organization_id,models.SubscribedServices.service_id == 6).first()

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




# define a route to get the orders of the store
@router.get('/shopify_store-orders/{store_id}',status_code=status.HTTP_200_OK)
async def get_store_orders(store_id:int,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
        
    #get the store api info from the database by store id and organization id
    shopify_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id,e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id,e_commerce_models.EcommerceIntegrations.store_type == "shopify").first()
    
    if not shopify_credentials:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="You have not connected to the store yet")
    
    #if there are not any orders in the database then add all the orders to the database

    if not db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.store_id == store_id,e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id,e_commerce_models.EcommerceOrder.store_type == "shopify").first():
                
        endpoint = f"https://{shopify_credentials.site_url}/admin/api/2023-10/orders.json"
         
        headers = { "X-Shopify-Access-Token": shopify_credentials.s_private_token }

        params = {"status":"any"}
            
        response = requests.get(endpoint,headers=headers,params=params)
        
        if response.status_code == 200:
            orders = response.json()["orders"]

            #change the type of order["id"] to string
            
            #add the orders to the database
            for order in orders:
                total = (order["total_price_set"]["shop_money"]["amount"])
                order_id = int(order["id"])
                customer_id = 0
                if order["customer"] is not None:
                    customer_id = order["customer"]["id"]

                order_to_add = e_commerce_models.EcommerceOrder(
                    store_id = store_id,
                    order_id = order["id"],
                    financial_status = order["financial_status"],
                    date_created = order["created_at"],
                    date_modified = order["updated_at"],
                    total = total,
                    prices = [float(price["price"]) for price in order["line_items"]],
                    email = order["contact_email"],
                    customer_note = order["note"],
                    line_items = [int(line_item["product_id"]) for line_item in order["line_items"]],
                    quantity = [quantity["quantity"] for quantity in order["line_items"]],
                    organization_id = current_user.organization_id,
                    sku = [sku["sku"] for sku in order["line_items"]],
                    store_type = "shopify",
                    s_cancelled_at = order["cancelled_at"],
                    s_cancel_reason = order["cancel_reason"],
                    currency = order["currency"],
                    s_fulfillment_status = order["fulfillment_status"],
                    ip_address = order["browser_ip"],
                    customer_id = customer_id
                )
                
                db.add(order_to_add)
                db.commit()
                db.refresh(order_to_add)
        
        return {"detail":"Orders added successfully"}
    
    else:
        #get the orders of the store after the last time the orders were added to the database according to the date_created column
        endpoint = f"https://{shopify_credentials.site_url}/admin/api/2023-10/orders.json"

        headers = { "X-Shopify-Access-Token": shopify_credentials.s_private_token }

        params = {"after": db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id,e_commerce_models.EcommerceOrder.store_id == store_id).order_by(e_commerce_models.EcommerceOrder.date_created.desc()).first().date_created.strftime("%Y-%m-%dT%H:%M:%S"),"status":"any"}

        response = requests.get(endpoint,headers=headers,params=params)

        if response.status_code == 200:
            orders = response.json()["orders"]

            #if there are no orders after the last date in db then return
            if orders == []:
                return {"detail":"No orders found"}

            last_date_in_db_created = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id==current_user.organization_id,e_commerce_models.EcommerceOrder.store_id==store_id).order_by(e_commerce_models.EcommerceOrder.date_created.desc()).first().date_created.strftime("%Y-%m-%dT%H:%M:%S")

            last_date_in_db_updated = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id==current_user.organization_id,e_commerce_models.EcommerceOrder.store_id==store_id).order_by(e_commerce_models.EcommerceOrder.date_modified.desc()).first().date_modified.strftime("%Y-%m-%dT%H:%M:%S")

            last_date = max(last_date_in_db_created,last_date_in_db_updated)

            #get the orders created after the last date in db
            orders = list(filter(lambda order: order["created_at"] > last_date, orders))

            #add the orders to the database
            for order in orders:

                #if order already exists in the database then skip
                if db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id,e_commerce_models.EcommerceOrder.store_id == store_id,e_commerce_models.EcommerceOrder.order_id == order["id"]).first():
                    continue

                total = (order["total_price_set"]["shop_money"]["amount"])
                order_id = int(order["id"])
                customer_id = 0
                if order["customer"]is not None:
                    customer_id = order["customer"]["id"]
                order_to_add = e_commerce_models.EcommerceOrder(
                    store_id = store_id,
                    order_id = order["id"],
                    financial_status = order["financial_status"],
                    date_created = order["created_at"],
                    date_modified = order["updated_at"],
                    total = total,
                    prices = [float(price["price"]) for price in order["line_items"]],
                    email = order["contact_email"],
                    customer_note = order["note"],
                    line_items = [int(line_item["product_id"]) for line_item in order["line_items"]],
                    quantity = [quantity["quantity"] for quantity in order["line_items"]],
                    organization_id = current_user.organization_id,
                    sku = [sku["sku"] for sku in order["line_items"]],
                    store_type = "shopify",
                    s_cancelled_at = order["cancelled_at"],
                    s_cancel_reason = order["cancel_reason"],
                    currency = order["currency"],
                    s_fulfillment_status = order["fulfillment_status"],
                    ip_address = order["browser_ip"],
                    customer_id = customer_id
                )
                
                db.add(order_to_add)
                db.commit()
                db.refresh(order_to_add)

            
            #get the orders updated after the last date in db
            orders = list(filter(lambda order: order["updated_at"] > last_date, orders))

            #update the orders in the database
            for order in orders:
                #update the modified order in the database
                db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id,e_commerce_models.EcommerceOrder.store_id == store_id,e_commerce_models.EcommerceOrder.order_id == order["id"]).update({"financial_status":order["financial_status"],"date_created":order["created_at"],"date_modified":order["updated_at"],"total":order["total_price_set"]["shop_money"]["amount"],"prices":[float(price["price"]) for price in order["line_items"]],"email":order["contact_email"],"customer_note":order["note"],"line_items":[(line_item["product_id"]) for line_item in order["line_items"]],"quantity":[quantity["quantity"] for quantity in order["line_items"]],"sku":[sku["sku"] for sku in order["line_items"]],"s_cancelled_at":order["cancelled_at"],"s_cancel_reason":order["cancel_reason"],"currency":order["currency"],"s_fulfillment_status":order["fulfillment_status"],"ip_address":order["browser_ip"],"customer_id":order["customer"]["id"]})

                db.commit()

            return {"detail":"Orders added successfully"}
        
        else:
            return {"detail":"Failed to get orders"}

        




# define a route to get the orders of the store
# @router.get('/ord/{store_id}',status_code=status.HTTP_200_OK)
# async def rev(store_id:int,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
        
#     #get the store api info from the database by store id and organization id
#     shopify_credentials = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id,e_commerce_models.EcommerceIntegrations.organization_id == current_user.organization_id,e_commerce_models.EcommerceIntegrations.store_type == "shopify").first()
    
#     if not shopify_credentials:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="You have not connected to the store yet")
    
#     #if there are not any orders in the database then add all the orders to the database
               
#     endpoint = f"https://{shopify_credentials.site_url}/admin/api/2023-10/orders.json"
         
#     headers = { "X-Shopify-Access-Token": shopify_credentials.s_private_token }

#     params = {"status":"any"}
            
#     response = requests.get(endpoint,headers=headers,params=params)
        
#     if response.status_code == 200:
#         orders = response.json()["orders"]

#         return orders
    
#     else:
#         return {"detail":"Failed to get orders"}

        