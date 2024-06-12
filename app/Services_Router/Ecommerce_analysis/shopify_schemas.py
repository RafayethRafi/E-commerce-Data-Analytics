from pydantic import BaseModel



class ShopifyCredentials(BaseModel):
    shopify_url : str
    s_private_token : str
    s_judgeme_api_token : str