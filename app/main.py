import sys
sys.stdout.flush()

from fastapi import FastAPI
from .routers import admin,user, auth,services,organization
from .Services_Router.Ecommerce_analysis import woocommerce_routers,shopify_routers
# from .Services_Router.Shopify_analysis import shopify_routers
from .Services_Router.text_analysis import text_analysis_main
from .Services_Router import dashboard,prediction
from .config import settings
from fastapi.middleware.cors import CORSMiddleware


# models.Base.metadata.create_all(bind=engine)


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(organization.router)
app.include_router(admin.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(services.router)
app.include_router(woocommerce_routers.router)
app.include_router(text_analysis_main.router)
app.include_router(shopify_routers.router)
app.include_router(dashboard.router)
app.include_router(prediction.router)

