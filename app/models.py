from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, Float, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from typing import Optional

Base = declarative_base()

# Association table for many-to-many relationship between Product and Category
product_category = Table(
    'product_category',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True, default=None)  # Soft delete timestamp

    # One-to-Many relationship: One User can have many Products
    products = relationship(
        "Product",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    
    # One-to-Many relationship: One User can have many Orders
    orders = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    price = Column(Float, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True, default=None)  # Soft delete timestamp

    # Foreign key for one-to-many relationship with User
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # One-to-Many relationship: Product belongs to one User
    owner = relationship("User", back_populates="products")

    # Many-to-Many relationship: Product can have many Categories
    categories = relationship(
        "Category",
        secondary=product_category,
        back_populates="products"
    )
    
    # Many-to-Many relationship: Product can be in many Orders (through OrderItem)
    # This is a many-to-many relationship with additional attributes (quantity, price)
    order_items = relationship("OrderItem", back_populates="product")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True, default=None)  # Soft delete timestamp

    # Many-to-Many relationship: Category can have many Products
    products = relationship(
        "Product",
        secondary=product_category,
        back_populates="categories"
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, completed, cancelled
    deleted_at = Column(DateTime, nullable=True, default=None)  # Soft delete timestamp

    # One-to-Many relationship: Order belongs to one User
    user = relationship("User", back_populates="orders")
    
    # One-to-Many relationship: Order can have many OrderItems
    # OrderItem is an association object that links Order and Product
    # with additional attributes (quantity, price)
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )


class OrderItem(Base):
    """
    Association Object for Many-to-Many relationship between Order and Product.
    
    This is different from a simple association table because it has additional
    attributes beyond just linking Order and Product:
    - quantity: How many of this product in the order
    - price: Price at the time of order (may differ from current product price)
    
    This pattern is used when the relationship itself needs to store data.
    """
    __tablename__ = "order_items"

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        primary_key=True
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True
    )

    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Price at time of order
    deleted_at = Column(DateTime, nullable=True, default=None)  # Soft delete timestamp

    # Many-to-One relationship: OrderItem belongs to one Order
    order = relationship("Order", back_populates="items")
    
    # Many-to-One relationship: OrderItem references one Product
    product = relationship("Product", back_populates="order_items")