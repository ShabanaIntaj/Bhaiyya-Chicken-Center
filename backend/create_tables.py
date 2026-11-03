
from app.database import Base, engine
from app.models import User, Product, orders

Base.metadata.create_all(bind=engine)

print("Database tables checked successfully!")
print("Users table is ready.")
print("Products table is ready.")
print("Orders table is ready.")
