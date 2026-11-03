
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.routes.auth import router as auth_router
from app.routes.product import router as product_router
from app.routes.orders import router as orders_router
from app.routes.shop import router as shop_router
from app.routes.daily_sales import router as daily_sales_router
from app.notifications import router as notifications_router


from app.database import Base, engine
from app.models.user import User
from app.models.product import Product
from app.models.orders import Order
from app.shop_settings import ShopSettings
from app.models.daily_sales import DailySales
from app.models.order_items import OrderItem

app = FastAPI(
    title="Bhaiyya Chicken Center API",
    description="Chicken shop ordering and management system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)

# Create the product image folder if it does not exist
UPLOAD_DIR = Path("uploads/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Serve uploaded product images through the browser
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads",
)

# Locate the frontend folder next to the backend folder
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"

# Serve frontend CSS and JavaScript files
app.mount(
    "/frontend-assets",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="frontend-assets",
)

app.include_router(auth_router)
app.include_router(product_router)
app.include_router(orders_router)
app.include_router(shop_router)
app.include_router(daily_sales_router)
app.include_router(notifications_router)




@app.get("/")
@app.get("/login")
def login_page():
    return FileResponse(str(FRONTEND_DIR / "login.html"))


@app.get("/index.html")
def home():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/health")
def health():
    return {"status": "healthy"}
