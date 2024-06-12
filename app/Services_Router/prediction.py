from .Ecommerce_analysis import e_commerce_models
from fastapi import Depends,APIRouter
from .. import oauth2
from sqlalchemy.orm import Session
from ..database import get_db
from .Ecommerce_analysis import e_commerce_models,woocommerce_routers,shopify_routers
import pandas as pd
from fastapi.encoders import jsonable_encoder


router = APIRouter(
    prefix= "/prediction",
    tags=['Dashboard']
)


# create an endpoint to get the order data from the database of a certain store_id of shopify
@router.get('/sales_prediction/{store_id}_{time}')
async def sales_prediction(store_id:int,time:str,db:Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
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

    order_data = db.query(e_commerce_models.EcommerceOrder).filter(e_commerce_models.EcommerceOrder.store_id == store_id).all()

    order_data = jsonable_encoder(order_data)
    
    


    # create a pandas dataframe of the order_data where there will be 3 columns ds which is datetime, y which is quantity and product_id
    data = pd.DataFrame(columns=["datetime","quantity","product_id","price"])
    for order in order_data:
        for i in range(len(order["line_items"])):
            data.loc[len(data)] = [order["date_created"], order["quantity"][i], order["line_items"][i],order["prices"][i]]

    # convert the ds column to datetime
    data["datetime"] = pd.to_datetime(data["datetime"])
    

    # Define smoothing parameter
    alpha = 0.5

    # Initialize dictionaries for forecasts and inventory
    product_forecasts = {}
    product_inventories = {}
    final_forecasts = []

    # Define functions for individual forecasting and inventory calculations
    def simple_exponential_smoothing(data, initial_forecast, alpha):
        smoothed_forecasts = []

        for i in range(len(data)):
            if i == 0:
                smoothed_forecast = initial_forecast
            else:
                previous_forecast = smoothed_forecasts[i - 1]
                previous_actual = data.iloc[i - 1]
                smoothed_forecast = alpha * previous_actual + (1 - alpha) * previous_forecast
            smoothed_forecasts.append(smoothed_forecast)
        return smoothed_forecasts

    # def calculate_inventory(forecasts, lead_time, safety_stock):
    #     inventory_levels = []
    #     for i in range(lead_time, len(forecasts) + lead_time):
    #         future_demand = sum(forecasts[i - lead_time:i])
    #         desired_inventory = future_demand + safety_stock
    #         inventory_levels.append(desired_inventory)
    #     return inventory_levels
    

    for product_id in data["product_id"].unique():
        # Filter data for current product
        product_data = data[data["product_id"] == product_id]
        
        # Resample data to daily level
        # daily_data = product_data.resample("D", on="datetime").agg(
        #     {"quantity": "sum", "price": "mean"}
        # )
        overall_data=[]
        # Resample data to weekly level
        if time == "weekly":
            overall_data = product_data.resample("W", on="datetime").agg(
            {"quantity": "sum", "price": "mean"}
            )
        elif time == "monthly":
            overall_data = product_data.resample("M", on="datetime").agg(
            {"quantity": "sum", "price": "mean"}
            )
        elif time == "yearly":
            overall_data = product_data.resample("Y", on="datetime").agg(
            {"quantity": "sum", "price": "mean"}
            )


        
        

        # Initialize product-specific variables
        initial_forecast = overall_data["quantity"].iloc[:3].mean()
   

        lead_time = 3  # Define lead time for this product
        safety_stock = 10  # Define safety stock for this product
        
        # Implement simple exponential smoothing for individual product
        smoothed_forecasts = simple_exponential_smoothing(
            overall_data["quantity"], initial_forecast, alpha
        )


        
        #add product_id as key and smoothed_forecast as value in the product_forecasts dictionary
        forecast = smoothed_forecasts[len(smoothed_forecasts)-1]
        #make this value rounded
        forecast = round(forecast)
        
        product_forecasts[f"{product_id}"] = forecast

    

    for x in product_forecasts:
        for product in products:
            if store_type == "woocommerce":
                if x == str(product["product_id"]):
                    final_forecasts.append({"product_name":product["product_name"],"product_id":product["product_id"],"quantity":product_forecasts[x]})
            elif store_type == "shopify":
                if x == str(product["product_id"]):
                    final_forecasts.append({"product_name":product["product_name"],"product_id":product["product_id"],"quantity":product_forecasts[x]})



        # # Calculate individual inventory needs
        # product_inventories[product_id] = calculate_inventory(
        #     smoothed_forecasts, lead_time, safety_stock
        # )

        # # Store product-specific forecasts
        # product_forecasts[product_id] = smoothed_forecasts

    
    return final_forecasts










# forecast_periods = 7  # One week
# smoothed_forecasts = simple_exponential_smoothing(
#     daily_data["quantity"], initial_forecast, alpha, forecast_periods
# )



# def simple_exponential_smoothing(data, initial_forecast, alpha, forecast_periods):
#     smoothed_forecasts = []
#     for i in range(len(data) + forecast_periods):
#         if i == 0:
#             smoothed_forecast = initial_forecast
#         elif i < len(data):
#             previous_forecast = smoothed_forecasts[i - 1]
#             previous_actual = data.iloc[i - 1]
#             smoothed_forecast = alpha * previous_actual + (1 - alpha) * previous_forecast
#         else:
#             # For future periods, the forecast is the last smoothed value
#             smoothed_forecast = smoothed_forecasts[i - 1]
#         smoothed_forecasts.append(smoothed_forecast)
#     return smoothed_forecasts