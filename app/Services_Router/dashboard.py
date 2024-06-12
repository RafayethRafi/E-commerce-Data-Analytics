from .Ecommerce_analysis import e_commerce_models
from fastapi import Depends,APIRouter
from .. import oauth2
from fastapi import Depends,APIRouter
from sqlalchemy.orm import Session
from ..database import get_db
import requests
from datetime import datetime,timedelta
from .Ecommerce_analysis import e_commerce_models,woocommerce_routers,shopify_routers,e_commerce_analysis_functions
import numpy as np
from fastapi.encoders import jsonable_encoder



router = APIRouter(
    prefix= "/dashboard",
    tags=['Dashboard']
)


#create an endpoint for the dashboard which will analyze the order data.It will get the order value per month in Y and X axis and will be able to do it for a selected year and return the results.
@router.get('/order_value_per_month/{year}_{store_id}}')
async def order_value_per_month(year:int,store_id:int,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    #check by the store id if the store belongs to woocommerce or shopify
    store_type = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id).first().store_type


    if store_type == "woocommerce":
        await woocommerce_routers.get_store_orders(store_id,db,current_user)
    elif store_type == "shopify":
        await shopify_routers.get_store_orders(store_id,db,current_user)

    # get the order data from e_commerece_orders table of the selected store_id
    order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.store_id == store_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime(year,1,1)).filter(e_commerce_models.EcommerceOrder.date_created <= datetime(year,12,31)).all()

    # create a list of month from january to december
    month_list = [i for i in range(1,13)]

    # use numpy and pandas. create a dictionary loop through the order data and identify which month it belongs to and then add the order total to the corresponding month and get a list of 12 months value
    order_value_per_month = np.zeros(12)
    for order in order_data:
        order_value_per_month[order.date_created.month-1] += order.total

    # create a dictionary with month as key and order value as value
    order_value_per_month_dict = dict(zip(month_list,order_value_per_month))
    

    # return the dictionary
    return {"order_value_per_month":order_value_per_month_dict, "year":year, "currency":order_data[0].currency}







#create a dashboard endpoint which will analyze the order data and get the top 10 most selling products for a selected time like a week or a month or 3 months a year
@router.get('/top_10_selling_products/{time}_{store_id}')
async def top_10_selling_products(time:str,store_id:int,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    #check by the store id if the store belongs to woocommerce or shopify
    store_type = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id).first().store_type

    products = []
    order_data = []

    if store_type == "woocommerce":
        await woocommerce_routers.get_store_orders(store_id,db,current_user)
        products = await woocommerce_routers.get_product(store_id,db,current_user)

    elif store_type == "shopify":
        await shopify_routers.get_store_orders(store_id,db,current_user)
        products = await shopify_routers.get_shopify_products(store_id,db,current_user)
        # products = products["products"]

    if products["error"]:
        return {"error":products["error"]}



    # get the order data from e_commerece_orders table of the selected store_id of last_week or last_month or last_3_months or last_year
    if time == "last_week":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.store_id == store_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=7)).all()
    elif time == "last_month":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.store_id == store_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=30)).all()
    elif time == "last_3_months":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.store_id == store_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=90)).all()
    elif time == "last_year":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.store_id == store_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=365)).all()

    order_data = jsonable_encoder(order_data)
    
    #create a dictionary of top 10 sold products by quantity by adding quantity of same product_id and then sort the dictionary by value and return the top 10 products
    product_quantity_dict = {}
    for order in order_data:
        for i in range(len(order["line_items"])):
            if order["line_items"][i] in product_quantity_dict:
                product_quantity_dict[order["line_items"][i]] += order["quantity"][i]
            else:
                product_quantity_dict[order["line_items"][i]] = order["quantity"][i]

    sorted_product_quantity_dict = dict(sorted(product_quantity_dict.items(), key=lambda item: item[1],reverse=True))
    top_10_selling_products = dict(list(sorted_product_quantity_dict.items())[:10])

    
    #map product_id from the top_10_selling_products dictionary to the product name from the products list and create a dictionary with product name as key and quantity as value
    top_10_selling_products_final = []
    
    return products
    
    for key,value in top_10_selling_products.items():
        for product in products:
            if key == product["product_id"]:
                top_10_selling_products_final.append({"product_name":product["product_name"],"product_id":product["product_id"],"quantity":value})

    
    #return the dictionary
    return top_10_selling_products_final





#create a dashboard endpoint which will analyze the order data and get the worst 10 most selling products for a selected time like a week or a month or 3 months a year
@router.get('/worst_10_selling_products/{time}_{store_id}')
async def worst_10_selling_products(time:str,store_id:int,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    #check by the store id if the store belongs to woocommerce or shopify
    store_type = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id).first().store_type

    products = []
    order_data = []

    if store_type == "woocommerce":
        await woocommerce_routers.get_store_orders(store_id,db,current_user)
        products = await woocommerce_routers.get_product(store_id,db,current_user)
    elif store_type == "shopify":
        await shopify_routers.get_store_orders(store_id,db,current_user)
        products = await shopify_routers.get_shopify_products(store_id,db,current_user)
        # products = products["products"]

    if products["error"]:
        return {"error":products["error"]}

    # get the order data from e_commerece_orders table of the selected store_id of last_week or last_month or last_3_months or last_year
    if time == "last_week":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.store_id == store_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=7)).all()
    elif time == "last_month":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.store_id == store_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=30)).all()
    elif time == "last_3_months":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.store_id == store_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=90)).all()
    elif time == "last_year":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.store_id == store_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=365)).all()

    order_data = jsonable_encoder(order_data)


    #create a dictionary of top 10 sold products by quantity by adding quantity of same product_id and then sort the dictionary by value and return the top 10 products
    product_quantity_dict = {}
    for order in order_data:
        for i in range(len(order["line_items"])):
            if order["line_items"][i] in product_quantity_dict:
                product_quantity_dict[order["line_items"][i]] += order["quantity"][i]
            else:
                product_quantity_dict[order["line_items"][i]] = order["quantity"][i]

    sorted_product_quantity_dict = dict(sorted(product_quantity_dict.items(), key=lambda item: item[1]))
    worst_10_selling_products = dict(list(sorted_product_quantity_dict.items())[:10])


    #map product_id from the top_10_selling_products dictionary to the product name from the products list and create a dictionary with product name as key and quantity as value
    worst_10_selling_products_final = []
    for key,value in worst_10_selling_products.items():
        for product in products:
            if key == product["product_id"]:
                worst_10_selling_products_final.append({"product_name":product["product_name"],"product_id":product["product_id"],"quantity":value})

    
    #return the dictionary
    return worst_10_selling_products_final







#create an endpoint to get the total order sentiment of the store for a selected time like a week or a month or 3 months a year and then get top 10 most positive and negative sentiment products
@router.get('/dashboard_order_sentiment_best/{time}_{store_id}')
async def dashboard_order_sentiment_best(time:str,store_id:int,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    #check by the store id if the store belongs to woocommerce or shopify
    store_type = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id).first().store_type

    products = []
    reviews = []

    if store_type == "woocommerce":
        reviews = await woocommerce_routers.get_store_reviews_for_dashboad(store_id,db,current_user)
        products = await woocommerce_routers.get_product(store_id,db,current_user)
    elif store_type == "shopify":
        reviews = await shopify_routers.get_store_reviews_for_dashboard(store_id,db,current_user)
        products = await shopify_routers.get_shopify_products(store_id,db,current_user)
        # products = products["products"]

    if products["error"]:
        return {"error":products["error"]}

    if time == "last_week":
        reviews = [review for review in reviews if datetime.strptime(review["date_created"],"%Y-%m-%d %H:%M:%S") >= datetime.now()-timedelta(days=7)]
    elif time == "last_month":
        reviews = [review for review in reviews if datetime.strptime(review["date_created"],"%Y-%m-%d %H:%M:%S")  >= datetime.now()-timedelta(days=30)]
    elif time == "last_3_months":
        reviews = [review for review in reviews if datetime.strptime(review["date_created"],"%Y-%m-%d %H:%M:%S")  >= datetime.now()-timedelta(days=90)]
    elif time == "last_year":
        reviews = [review for review in reviews if datetime.strptime(review["date_created"],"%Y-%m-%d %H:%M:%S")  >= datetime.now()-timedelta(days=365)]

    overall_sentiment = e_commerce_analysis_functions.reviewAnalysis(reviews)

    #create a dictionary of top 10 most positive sentiment products
    product_wise_sentiment = {}
    for review in reviews:
        if review["product_id"] in product_wise_sentiment:
            product_wise_sentiment[review["product_id"]].append(review)
        else:
            product_wise_sentiment[review["product_id"]] = [review]

    product_wise_sentiment_analysis = {}
    for key,value in product_wise_sentiment.items():
        product_wise_sentiment_analysis[key] = e_commerce_analysis_functions.reviewAnalysis(value)

    #sort the dictionary by value of pos_per and get top 10 products
    sorted_product_wise_sentiment_analysis = dict(sorted(product_wise_sentiment_analysis.items(), key=lambda item: item[1]["pos_per"],reverse=True))
    sorted_product_wise_sentiment_analysis = dict(list(sorted_product_wise_sentiment_analysis.items())[:10])
    

    #map product_id from the top_10_selling_products dictionary to the product name from the products list and create a dictionary with product name as key and quantity as value
    top_10_positive_sentiment_products = []
    for key,value in sorted_product_wise_sentiment_analysis.items():
        for product in products:
            if key == product["product_id"]:
                top_10_positive_sentiment_products.append({"product_name":product["product_name"],"product_id":product["product_id"],"pos_per":value["pos_per"],"neg_per":value["neg_per"],"neu_per":value["neu_per"]})


    #create json containing overall sentiment and top 10 positive sentiment products
    data = {
        # "overall_sentiment":overall_sentiment,
        "top_10_positive_sentiment_products":top_10_positive_sentiment_products
    }

    return data

@router.get('/dashboard_order_sentiment_worst/{time}_{store_id}')
async def dashboard_order_sentiment_worst(time:str,store_id:int,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    #check by the store id if the store belongs to woocommerce or shopify
    store_type = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id).first().store_type

    products = []
    reviews = []

    if store_type == "woocommerce":
        reviews = await woocommerce_routers.get_store_reviews_for_dashboad(store_id,db,current_user)
        products = await woocommerce_routers.get_product(store_id,db,current_user)
    elif store_type == "shopify":
        reviews = await shopify_routers.get_store_reviews_for_dashboard(store_id,db,current_user)
        products = await shopify_routers.get_shopify_products(store_id,db,current_user)
        # products = products["products"]

    if products["error"]:
        return {"error":products["error"]}

    if time == "last_week":
        reviews = [review for review in reviews if datetime.strptime(review["date_created"],"%Y-%m-%d %H:%M:%S") >= datetime.now()-timedelta(days=7)]
    elif time == "last_month":
        reviews = [review for review in reviews if datetime.strptime(review["date_created"],"%Y-%m-%d %H:%M:%S")  >= datetime.now()-timedelta(days=30)]
    elif time == "last_3_months":
        reviews = [review for review in reviews if datetime.strptime(review["date_created"],"%Y-%m-%d %H:%M:%S")  >= datetime.now()-timedelta(days=90)]
    elif time == "last_year":
        reviews = [review for review in reviews if datetime.strptime(review["date_created"],"%Y-%m-%d %H:%M:%S")  >= datetime.now()-timedelta(days=365)]

    overall_sentiment = e_commerce_analysis_functions.reviewAnalysis(reviews)

    #create a dictionary of top 10 most positive sentiment products
    product_wise_sentiment = {}
    for review in reviews:
        if review["product_id"] in product_wise_sentiment:
            product_wise_sentiment[review["product_id"]].append(review)
        else:
            product_wise_sentiment[review["product_id"]] = [review]

    product_wise_sentiment_analysis = {}
    for key,value in product_wise_sentiment.items():
        product_wise_sentiment_analysis[key] = e_commerce_analysis_functions.reviewAnalysis(value)

    #sort the dictionary by value of pos_per and get top 10 products
    sorted_product_wise_sentiment_analysis = dict(sorted(product_wise_sentiment_analysis.items(), key=lambda item: item[1]["pos_per"],reverse=False))
    sorted_product_wise_sentiment_analysis = dict(list(sorted_product_wise_sentiment_analysis.items())[:10])

    #map product_id from the top_10_selling_products dictionary to the product name from the products list and create a dictionary with product name as key and quantity as value
    worst_10_positive_sentiment_products = []
    for key,value in sorted_product_wise_sentiment_analysis.items():
        for product in products:
            if key == product["product_id"]:
                worst_10_positive_sentiment_products.append({"product_name":product["product_name"],"product_id":product["product_id"],"pos_per":value["pos_per"],"neg_per":value["neg_per"],"neu_per":value["neu_per"]})


    #create json containing overall sentiment and top 10 positive sentiment products
    data = {
        # "overall_sentiment":overall_sentiment,
        "worst_10_positive_sentiment_products":worst_10_positive_sentiment_products
    }

    return data



#freeCodeCamp.org er ta
#https://www.freecodecamp.org/news/how-to-get-location-information-of-ip-address-using-python/
# get locations from from the ip address of order data
# @router.get('/order_locations/{time}_{store_id}')
# async def order_locations(time:str,store_id:int,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    
#     ip = "103.186.219.29"
#     response = requests.get(f'https://ipapi.co/{ip}/json/').json()
#     location_data = {
#         "ip": ip,
#         "city": response.get("city"),
#         "region": response.get("region"),
#         "country": response.get("country_name")
#     }
#     return location_data


# get locations latititude and longitude from from the ip address of order data
@router.get('/order_locations/{time}_{store_id}')
async def order_locations(time:str,store_id:int,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
        
        #check by the store id if the store belongs to woocommerce or shopify
    store_type = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id).first().store_type
    
    order_data = []
    
    if store_type == "woocommerce":
        order_data = await woocommerce_routers.get_store_orders(store_id,db,current_user)
    elif store_type == "shopify":
        order_data =  await shopify_routers.get_store_orders(store_id,db,current_user)

    
    # get the order data from e_commerece_orders table of the selected store_id of last_week or last_month or last_3_months or last_year
    if time == "last_week":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.store_id == store_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=7)).all()
    elif time == "last_month":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.store_id == store_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=30)).all()
    elif time == "last_3_months":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.store_id == store_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=90)).all()
    elif time == "last_year":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.store_id == store_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=365)).all()
    
    order_data = jsonable_encoder(order_data)
    
    #create a list of ip address from the order data
    # ip_address_list = []
    # for order in order_data:
    #     ip_address_list.append(order["ip_address"])
    
    #create a dictionary of ip address and location data and calculate the total order value from the same ip address from order data
    location_data = {}
    for order in order_data:
        if order["ip_address"] == "":
            continue
        if order["ip_address"] in location_data:
            location_data[order["ip_address"]]["total_order_value"] += order["total"]
        else:
            location_data[order["ip_address"]] = {
                "total_order_value":order["total"]
            }


    # in the location data dictionary add the location data from the ip address as the ip address is the key of the dictionary
    for key in location_data:
        response = requests.get(f'https://ipapi.co/{key}/json/').json()
        location_data[key]["city"] = response.get("city")
        location_data[key]["region"] = response.get("region")
        location_data[key]["country"] = response.get("country_name")
        location_data[key]["latitude"] = response.get("latitude")
        location_data[key]["longitude"] = response.get("longitude")


    
    return location_data





#create an enpoint to figure out which products has the most returning customers
@router.get('/most_returning_customers/{time}_{store_id}')
async def most_returning_customers(time:str,store_id:int,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    #check by the store id if the store belongs to woocommerce or shopify
    store_type = db.query(e_commerce_models.EcommerceIntegrations).filter(e_commerce_models.EcommerceIntegrations.id == store_id).first().store_type

    order_data = []
    products = []

    if store_type == "woocommerce":
        order_data = await woocommerce_routers.get_store_orders(store_id,db,current_user)
        products = await woocommerce_routers.get_product(store_id,db,current_user)

    elif store_type == "shopify":
        order_data = await shopify_routers.get_store_orders(store_id,db,current_user)
        products = await shopify_routers.get_shopify_products(store_id,db,current_user)
        # products = products["products"]

    if products["error"]:
        return {"error":products["error"]}

    # get the order data from e_commerece_orders table of the selected store_id of last_week or last_month or last_3_months or last_year
    if time == "last_week":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=7)).all()
    elif time == "last_month":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=30)).all()
    elif time == "last_3_months":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=90)).all()
    elif time == "last_year":
        order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.organization_id == current_user.organization_id).filter(e_commerce_models.EcommerceOrder.date_created >= datetime.now()-timedelta(days=365)).all()

    order_data = jsonable_encoder(order_data)

    #create a dictionary of product_id and a dict of customer_id and quantity
    returning_customer_dict = {}
    for order in order_data:
        for i in range(len(order["line_items"])):
            if order["line_items"][i] in returning_customer_dict:
                if order["customer_id"] == 0:
                    continue
                if order["customer_id"] in returning_customer_dict[order["line_items"][i]]:
                    returning_customer_dict[order["line_items"][i]][order["customer_id"]] += 1
                else:
                    returning_customer_dict[order["line_items"][i]][order["customer_id"]] = 0
            else:
                if order["customer_id"] == 0:
                    continue
                returning_customer_dict[order["line_items"][i]] = {
                    order["customer_id"]: 0
                }

    # filter out the customers who has ordered only once
    keys_to_delete = []
    for key, value in returning_customer_dict.items():
        for key2, value2 in value.items():
            if value2 == 0:
                keys_to_delete.append((key, key2))

    for key, key2 in keys_to_delete:
        del returning_customer_dict[key][key2]

    #sort the dictionary by the number of customers and get the top 10 products
    sorted_returning_customer_dict = dict(sorted(returning_customer_dict.items(), key=lambda item: len(item[1]),reverse=True))
    top_10_returning_customers = dict(list(sorted_returning_customer_dict.items())[:10])

    

    #create a dictionary where the key product_id is replaced with product name
    returning_customer_dict_product_name = {}
    for key,value in returning_customer_dict.items():
        for product in products:
            if key == product["product_id"]:
                returning_customer_dict_product_name[product["product_name"]] = value

    
    return returning_customer_dict_product_name


