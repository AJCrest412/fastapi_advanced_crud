from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import or_, and_
from typing import Optional, List
from fastapi import HTTPException
from datetime import datetime
from app.models import User, Product, Category, Order, OrderItem
from app import schemas


def filter_not_deleted(query, model_class, include_deleted: bool = False):
    if not include_deleted:
        query = query.filter(model_class.deleted_at.is_(None))
    return query


def create_user(db: Session, user_data: schemas.UserCreate) -> User:
    existing_user = db.query(User).filter(
        User.email == user_data.email,
        User.deleted_at.is_(None)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    user = User(email=user_data.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int, include_deleted: bool = False) -> Optional[User]:
    query = db.query(User).filter(User.id == user_id)
    query = filter_not_deleted(query, User, include_deleted)
    return query.first()


def get_user_with_products(db: Session, user_id: int, include_deleted: bool = False) -> Optional[User]:
    query = (
        db.query(User)
        .options(selectinload(User.products))
        .filter(User.id == user_id)
    )
    query = filter_not_deleted(query, User, include_deleted)
    return query.first()


def get_users(
    db: Session,
    params: schemas.UserQueryParams
) -> tuple[List[User], int]:
    query = db.query(User)
    query = filter_not_deleted(query, User, params.include_deleted)
    
    if params.email:
        query = query.filter(User.email.ilike(f"%{params.email}%"))
    
    total = query.count()
    users = query.offset(params.skip).limit(params.limit).all()
    
    return users, total


def get_users_with_products(
    db: Session,
    params: schemas.PaginationQueryParams,
    include_deleted: bool = False
) -> tuple[List[User], int]:
    query = db.query(User).options(selectinload(User.products))
    query = filter_not_deleted(query, User, include_deleted)
    total = query.count()
    users = query.offset(params.skip).limit(params.limit).all()
    return users, total


def soft_delete_user(db: Session, user_id: int) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        return None
    
    user.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def restore_user(db: Session, user_id: int) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id, User.deleted_at.isnot(None)).first()
    if not user:
        return None
    
    user.deleted_at = None
    db.commit()
    db.refresh(user)
    return user


# ============ Product CRUD Operations ============
# 
# PATTERN: Using Pydantic Schemas Instead of Individual Parameters
# ===============================================================
# 
# When functions have many parameters (5+), it's better to use Pydantic schemas:
# 
# ❌ BAD (Many parameters - hard to maintain):
# def create_product(db, name, owner_id, description, price, category_ids, 
#                    stock, sku, weight, dimensions, tags, ...):
#     # Too many parameters!
# 
# ✅ GOOD (Schema object - clean and maintainable):
# def create_product(db, product_data: schemas.ProductCreate):
#     # Single parameter, type-safe, easy to extend
# 
# Benefits:
# 1. Single parameter instead of many
# 2. Type validation happens automatically
# 3. Easy to add new fields (just update schema)
# 4. Self-documenting (schema shows all fields)
# 5. Reusable (schema used in multiple places)
# 6. Better IDE support (autocomplete, type hints)
#
def create_product(
    db: Session,
    product_data: schemas.ProductCreate
) -> Product:
    owner = db.query(User).filter(User.id == product_data.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    
    product = Product(
        name=product_data.name,
        owner_id=product_data.owner_id,
        description=product_data.description,
        price=product_data.price,
        is_active=True
    )
    
    if product_data.category_ids:
        categories = db.query(Category).filter(Category.id.in_(product_data.category_ids)).all()
        if len(categories) != len(product_data.category_ids):
            raise HTTPException(status_code=404, detail="One or more categories not found")
        product.categories = categories
    
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_product(db: Session, product_id: int, include_deleted: bool = False) -> Optional[Product]:
    """Get a single product by ID"""
    query = db.query(Product).filter(Product.id == product_id)
    query = filter_not_deleted(query, Product, include_deleted)
    return query.first()


def get_product_with_owner(db: Session, product_id: int, include_deleted: bool = False) -> Optional[Product]:
    """Get product with owner loaded (many-to-one relationship)"""
    query = (
        db.query(Product)
        .options(joinedload(Product.owner))
        .filter(Product.id == product_id)
    )
    query = filter_not_deleted(query, Product, include_deleted)
    return query.first()


def get_product_with_categories(db: Session, product_id: int, include_deleted: bool = False) -> Optional[Product]:
    query = (
        db.query(Product)
        .options(selectinload(Product.categories))
        .filter(Product.id == product_id)
    )
    query = filter_not_deleted(query, Product, include_deleted)
    return query.first()


def get_product_full(db: Session, product_id: int, include_deleted: bool = False) -> Optional[Product]:
    query = (
        db.query(Product)
        .options(
            joinedload(Product.owner),
            selectinload(Product.categories)
        )
        .filter(Product.id == product_id)
    )
    query = filter_not_deleted(query, Product, include_deleted)
    return query.first()


def get_products(
    db: Session,
    params: schemas.ProductQueryParams
) -> tuple[List[Product], int]:
    query = db.query(Product)
    query = filter_not_deleted(query, Product, params.include_deleted)
    
    if params.name:
        query = query.filter(Product.name.ilike(f"%{params.name}%"))
    
    if params.owner_id is not None:
        query = query.filter(Product.owner_id == params.owner_id)
    
    if params.is_active is not None:
        query = query.filter(Product.is_active == params.is_active)
    
    if params.min_price is not None:
        query = query.filter(Product.price >= params.min_price)
    
    if params.max_price is not None:
        query = query.filter(Product.price <= params.max_price)
    
    if params.category_id is not None:
        query = query.join(Product.categories).filter(Category.id == params.category_id)
    
    total = query.count()
    products = query.offset(params.skip).limit(params.limit).all()
    
    return products, total


def get_products_with_owner(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    include_deleted: bool = False
) -> tuple[List[Product], int]:
    """Get products with owner loaded"""
    query = db.query(Product).options(joinedload(Product.owner))
    query = filter_not_deleted(query, Product, include_deleted)
    total = query.count()
    products = query.offset(skip).limit(limit).all()
    return products, total


def get_products_with_categories(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    include_deleted: bool = False
) -> tuple[List[Product], int]:
    """Get products with categories loaded"""
    query = db.query(Product).options(selectinload(Product.categories))
    query = filter_not_deleted(query, Product, include_deleted)
    total = query.count()
    products = query.offset(skip).limit(limit).all()
    return products, total


def update_product(
    db: Session,
    product_id: int,
    product_update: schemas.ProductUpdate
) -> Optional[Product]:
    """
    Update a product and its categories.
    
    This function accepts a Pydantic schema object instead of individual parameters.
    Benefits:
    1. Only provided fields need to be updated (Pydantic handles None values)
    2. Easy to extend - add fields to schema without changing function signature
    3. Type validation happens automatically
    4. Cleaner code - no need to check each parameter individually
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    
    # Update only provided fields using model_dump(exclude_unset=True)
    # This only includes fields that were explicitly set (not None defaults)
    update_data = product_update.model_dump(exclude_unset=True, exclude={'category_ids'})
    
    for field, value in update_data.items():
        setattr(product, field, value)
    
    # Update categories (many-to-many relationship) if provided
    if product_update.category_ids is not None:
        categories = db.query(Category).filter(Category.id.in_(product_update.category_ids)).all()
        if len(categories) != len(product_update.category_ids):
            raise HTTPException(status_code=404, detail="One or more categories not found")
        product.categories = categories
    
    db.commit()
    db.refresh(product)
    return product


def soft_delete_product(db: Session, product_id: int) -> Optional[Product]:
    """Soft delete a product by setting deleted_at timestamp"""
    product = db.query(Product).filter(Product.id == product_id, Product.deleted_at.is_(None)).first()
    if not product:
        return None
    
    product.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    return product


def restore_product(db: Session, product_id: int) -> Optional[Product]:
    """Restore a soft-deleted product by clearing deleted_at"""
    product = db.query(Product).filter(Product.id == product_id, Product.deleted_at.isnot(None)).first()
    if not product:
        return None
    
    product.deleted_at = None
    db.commit()
    db.refresh(product)
    return product


# ============ Category CRUD Operations ============
def create_category(
    db: Session,
    category_data: schemas.CategoryCreate
) -> Category:
    existing_category = db.query(Category).filter(Category.name == category_data.name).first()
    if existing_category:
        raise HTTPException(status_code=400, detail="Category with this name already exists")
    
    category = Category(name=category_data.name, description=category_data.description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def get_category(db: Session, category_id: int, include_deleted: bool = False) -> Optional[Category]:
    """Get a single category by ID"""
    query = db.query(Category).filter(Category.id == category_id)
    query = filter_not_deleted(query, Category, include_deleted)
    return query.first()


def get_category_with_products(db: Session, category_id: int, include_deleted: bool = False) -> Optional[Category]:
    """Get category with products loaded (many-to-many relationship)"""
    query = (
        db.query(Category)
        .options(selectinload(Category.products))
        .filter(Category.id == category_id)
    )
    query = filter_not_deleted(query, Category, include_deleted)
    return query.first()


def get_categories(
    db: Session,
    params: schemas.CategoryQueryParams
) -> tuple[List[Category], int]:
    query = db.query(Category)
    query = filter_not_deleted(query, Category, params.include_deleted)
    
    if params.name:
        query = query.filter(Category.name.ilike(f"%{params.name}%"))
    
    total = query.count()
    categories = query.offset(params.skip).limit(params.limit).all()
    
    return categories, total


def get_categories_with_products(
    db: Session,
    params: schemas.PaginationQueryParams,
    include_deleted: bool = False
) -> tuple[List[Category], int]:
    query = db.query(Category).options(selectinload(Category.products))
    query = filter_not_deleted(query, Category, include_deleted)
    total = query.count()
    categories = query.offset(params.skip).limit(params.limit).all()
    return categories, total


def soft_delete_category(db: Session, category_id: int) -> Optional[Category]:
    """Soft delete a category by setting deleted_at timestamp"""
    category = db.query(Category).filter(Category.id == category_id, Category.deleted_at.is_(None)).first()
    if not category:
        return None
    
    category.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(category)
    return category


def restore_category(db: Session, category_id: int) -> Optional[Category]:
    """Restore a soft-deleted category by clearing deleted_at"""
    category = db.query(Category).filter(Category.id == category_id, Category.deleted_at.isnot(None)).first()
    if not category:
        return None
    
    category.deleted_at = None
    db.commit()
    db.refresh(category)
    return category


def create_order(
    db: Session,
    order_data: schemas.OrderCreate
) -> Order:
    user = db.query(User).filter(User.id == order_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    order = Order(
        user_id=order_data.user_id,
        status=order_data.status
    )
    db.add(order)
    db.flush()
    
    for item_data in order_data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with id {item_data.product_id} not found"
            )
        
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            price=item_data.price
        )
        db.add(order_item)
    
    db.commit()
    db.refresh(order)
    return order


def get_order(db: Session, order_id: int, include_deleted: bool = False) -> Optional[Order]:
    """Get a single order by ID"""
    query = db.query(Order).filter(Order.id == order_id)
    query = filter_not_deleted(query, Order, include_deleted)
    return query.first()


def get_order_with_items(db: Session, order_id: int, include_deleted: bool = False) -> Optional[Order]:
    """Get order with order items loaded (one-to-many relationship)"""
    query = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.id == order_id)
    )
    query = filter_not_deleted(query, Order, include_deleted)
    return query.first()


def get_order_with_items_and_products(db: Session, order_id: int, include_deleted: bool = False) -> Optional[Order]:
    """
    Get order with items and products loaded.
    
    Demonstrates:
    - One-to-Many: Order -> OrderItems
    - Many-to-One: OrderItem -> Product
    - Many-to-Many through association object: Order <-> Product (via OrderItem)
    """
    query = (
        db.query(Order)
        .options(
            selectinload(Order.items).joinedload(OrderItem.product)
        )
        .filter(Order.id == order_id)
    )
    query = filter_not_deleted(query, Order, include_deleted)
    return query.first()


def get_order_full(db: Session, order_id: int, include_deleted: bool = False) -> Optional[Order]:
    """
    Get order with user, items, and products (all relationships).
    
    Demonstrates loading multiple relationship levels:
    - Order -> User (many-to-one)
    - Order -> OrderItems (one-to-many)
    - OrderItem -> Product (many-to-one)
    """
    query = (
        db.query(Order)
        .options(
            joinedload(Order.user),
            selectinload(Order.items).joinedload(OrderItem.product)
        )
        .filter(Order.id == order_id)
    )
    query = filter_not_deleted(query, Order, include_deleted)
    return query.first()


def get_orders(
    db: Session,
    params: schemas.OrderQueryParams
) -> tuple[List[Order], int]:
    query = db.query(Order)
    query = filter_not_deleted(query, Order, params.include_deleted)
    
    if params.user_id is not None:
        query = query.filter(Order.user_id == params.user_id)
    
    if params.status is not None:
        query = query.filter(Order.status == params.status)
    
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(params.skip).limit(params.limit).all()
    
    return orders, total


def get_orders_with_items(
    db: Session,
    params: schemas.PaginationQueryParams,
    include_deleted: bool = False
) -> tuple[List[Order], int]:
    query = db.query(Order).options(selectinload(Order.items))
    query = filter_not_deleted(query, Order, include_deleted)
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(params.skip).limit(params.limit).all()
    return orders, total


def get_orders_with_items_and_products(
    db: Session,
    params: schemas.PaginationQueryParams,
    include_deleted: bool = False
) -> tuple[List[Order], int]:
    query = (
        db.query(Order)
        .options(selectinload(Order.items).joinedload(OrderItem.product))
    )
    query = filter_not_deleted(query, Order, include_deleted)
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(params.skip).limit(params.limit).all()
    return orders, total


def update_order(
    db: Session,
    order_id: int,
    order_update: schemas.OrderUpdate
) -> Optional[Order]:
    order = db.query(Order).filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not order:
        return None
    
    update_data = order_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    db.commit()
    db.refresh(order)
    return order


def soft_delete_order(db: Session, order_id: int) -> Optional[Order]:
    """Soft delete an order by setting deleted_at timestamp"""
    order = db.query(Order).filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not order:
        return None
    
    order.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order


def restore_order(db: Session, order_id: int) -> Optional[Order]:
    """Restore a soft-deleted order by clearing deleted_at"""
    order = db.query(Order).filter(Order.id == order_id, Order.deleted_at.isnot(None)).first()
    if not order:
        return None
    
    order.deleted_at = None
    db.commit()
    db.refresh(order)
    return order


def get_user_orders(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    include_deleted: bool = False
) -> tuple[List[Order], int]:
    """Get all orders for a specific user"""
    query = db.query(Order).filter(Order.user_id == user_id)
    query = filter_not_deleted(query, Order, include_deleted)
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders, total


def get_product_orders(
    db: Session,
    product_id: int,
    skip: int = 0,
    limit: int = 10,
    include_deleted: bool = False
) -> tuple[List[Order], int]:
    """
    Get all orders containing a specific product.
    
    Demonstrates querying many-to-many relationship through association object.
    """
    query = (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.product_id == product_id)
    )
    query = filter_not_deleted(query, Order, include_deleted)
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders, total