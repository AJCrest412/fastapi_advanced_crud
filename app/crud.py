from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select, func, and_
from typing import Optional, List
from fastapi import HTTPException
from datetime import datetime
from app.models import User, Product, Category, Order, OrderItem
from app import schemas


def filter_not_deleted(stmt, model_class, include_deleted: bool = False):
    if not include_deleted:
        stmt = stmt.where(model_class.deleted_at.is_(None))
    return stmt


async def create_user(db: AsyncSession, user_data: schemas.UserCreate) -> User:
    stmt = select(User).where(
        User.email == user_data.email,
        User.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    user = User(email=user_data.email)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user(db: AsyncSession, user_id: int, include_deleted: bool = False) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    stmt = filter_not_deleted(stmt, User, include_deleted)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_with_products(db: AsyncSession, user_id: int, include_deleted: bool = False) -> Optional[User]:
    stmt = (
        select(User)
        .options(selectinload(User.products))
        .where(User.id == user_id)
    )
    stmt = filter_not_deleted(stmt, User, include_deleted)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_users(
    db: AsyncSession,
    params: schemas.UserQueryParams
) -> tuple[List[User], int]:
    stmt = select(User)
    stmt = filter_not_deleted(stmt, User, params.include_deleted)
    
    if params.email:
        stmt = stmt.where(User.email.ilike(f"%{params.email}%"))
    
    count_stmt = select(func.count(User.id))
    count_stmt = filter_not_deleted(count_stmt, User, params.include_deleted)
    if params.email:
        count_stmt = count_stmt.where(User.email.ilike(f"%{params.email}%"))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.offset(params.skip).limit(params.limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return list(users), total


async def get_users_with_products(
    db: AsyncSession,
    params: schemas.PaginationQueryParams,
    include_deleted: bool = False
) -> tuple[List[User], int]:
    stmt = select(User).options(selectinload(User.products))
    stmt = filter_not_deleted(stmt, User, include_deleted)
    
    count_stmt = select(func.count(User.id))
    count_stmt = filter_not_deleted(count_stmt, User, include_deleted)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.offset(params.skip).limit(params.limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return list(users), total


async def soft_delete_user(db: AsyncSession, user_id: int) -> Optional[User]:
    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return None
    
    user.deleted_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user


async def restore_user(db: AsyncSession, user_id: int) -> Optional[User]:
    stmt = select(User).where(User.id == user_id, User.deleted_at.isnot(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return None
    
    user.deleted_at = None
    await db.commit()
    await db.refresh(user)
    return user


async def create_product(
    db: AsyncSession,
    product_data: schemas.ProductCreate
) -> Product:
    stmt = select(User).where(User.id == product_data.owner_id)
    result = await db.execute(stmt)
    owner = result.scalar_one_or_none()
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
        stmt = select(Category).where(Category.id.in_(product_data.category_ids))
        result = await db.execute(stmt)
        categories = result.scalars().all()
        if len(categories) != len(product_data.category_ids):
            raise HTTPException(status_code=404, detail="One or more categories not found")
        product.categories = list(categories)
    
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def get_product(db: AsyncSession, product_id: int, include_deleted: bool = False) -> Optional[Product]:
    stmt = select(Product).where(Product.id == product_id)
    stmt = filter_not_deleted(stmt, Product, include_deleted)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_product_with_owner(db: AsyncSession, product_id: int, include_deleted: bool = False) -> Optional[Product]:
    stmt = (
        select(Product)
        .options(joinedload(Product.owner))
        .where(Product.id == product_id)
    )
    stmt = filter_not_deleted(stmt, Product, include_deleted)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_product_with_categories(db: AsyncSession, product_id: int, include_deleted: bool = False) -> Optional[Product]:
    stmt = (
        select(Product)
        .options(selectinload(Product.categories))
        .where(Product.id == product_id)
    )
    stmt = filter_not_deleted(stmt, Product, include_deleted)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_product_full(db: AsyncSession, product_id: int, include_deleted: bool = False) -> Optional[Product]:
    stmt = (
        select(Product)
        .options(
            joinedload(Product.owner),
            selectinload(Product.categories)
        )
        .where(Product.id == product_id)
    )
    stmt = filter_not_deleted(stmt, Product, include_deleted)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_products(
    db: AsyncSession,
    params: schemas.ProductQueryParams
) -> tuple[List[Product], int]:
    stmt = select(Product)
    stmt = filter_not_deleted(stmt, Product, params.include_deleted)
    
    if params.name:
        stmt = stmt.where(Product.name.ilike(f"%{params.name}%"))
    
    if params.owner_id is not None:
        stmt = stmt.where(Product.owner_id == params.owner_id)
    
    if params.is_active is not None:
        stmt = stmt.where(Product.is_active == params.is_active)
    
    if params.min_price is not None:
        stmt = stmt.where(Product.price >= params.min_price)
    
    if params.max_price is not None:
        stmt = stmt.where(Product.price <= params.max_price)
    
    if params.category_id is not None:
        stmt = stmt.join(Product.categories).where(Category.id == params.category_id)
    
    count_stmt = select(func.count(Product.id))
    count_stmt = filter_not_deleted(count_stmt, Product, params.include_deleted)
    if params.name:
        count_stmt = count_stmt.where(Product.name.ilike(f"%{params.name}%"))
    if params.owner_id is not None:
        count_stmt = count_stmt.where(Product.owner_id == params.owner_id)
    if params.is_active is not None:
        count_stmt = count_stmt.where(Product.is_active == params.is_active)
    if params.min_price is not None:
        count_stmt = count_stmt.where(Product.price >= params.min_price)
    if params.max_price is not None:
        count_stmt = count_stmt.where(Product.price <= params.max_price)
    if params.category_id is not None:
        count_stmt = count_stmt.join(Product.categories).where(Category.id == params.category_id)
    
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.offset(params.skip).limit(params.limit)
    result = await db.execute(stmt)
    products = result.scalars().all()
    
    return list(products), total


async def get_products_with_owner(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    include_deleted: bool = False
) -> tuple[List[Product], int]:
    stmt = select(Product).options(joinedload(Product.owner))
    stmt = filter_not_deleted(stmt, Product, include_deleted)
    
    count_stmt = select(func.count(Product.id))
    count_stmt = await filter_not_deleted(count_stmt, Product, include_deleted)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().all()
    return list(products), total


async def get_products_with_categories(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    include_deleted: bool = False
) -> tuple[List[Product], int]:
    stmt = select(Product).options(selectinload(Product.categories))
    stmt = filter_not_deleted(stmt, Product, include_deleted)
    
    count_stmt = select(func.count(Product.id))
    count_stmt = await filter_not_deleted(count_stmt, Product, include_deleted)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().all()
    return list(products), total


async def update_product(
    db: AsyncSession,
    product_id: int,
    product_update: schemas.ProductUpdate
) -> Optional[Product]:
    stmt = select(Product).options(selectinload(Product.categories)).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        return None
    
    update_data = product_update.model_dump(exclude_unset=True, exclude={'category_ids'})
    for field, value in update_data.items():
        setattr(product, field, value)
    
    if product_update.category_ids is not None:
        stmt = select(Category).where(Category.id.in_(product_update.category_ids))
        result = await db.execute(stmt)
        categories = result.scalars().all()
        if len(categories) != len(product_update.category_ids):
            raise HTTPException(status_code=404, detail="One or more categories not found")
        product.categories = list(categories)
    
    await db.commit()
    await db.refresh(product)
    return product


async def soft_delete_product(db: AsyncSession, product_id: int) -> Optional[Product]:
    stmt = select(Product).where(Product.id == product_id, Product.deleted_at.is_(None))
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        return None
    
    product.deleted_at = datetime.utcnow()
    await db.commit()
    await db.refresh(product)
    return product


async def restore_product(db: AsyncSession, product_id: int) -> Optional[Product]:
    stmt = select(Product).where(Product.id == product_id, Product.deleted_at.isnot(None))
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        return None
    
    product.deleted_at = None
    await db.commit()
    await db.refresh(product)
    return product


async def create_category(
    db: AsyncSession,
    category_data: schemas.CategoryCreate
) -> Category:
    stmt = select(Category).where(Category.name == category_data.name)
    result = await db.execute(stmt)
    existing_category = result.scalar_one_or_none()
    if existing_category:
        raise HTTPException(status_code=400, detail="Category with this name already exists")
    
    category = Category(name=category_data.name, description=category_data.description)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def get_category(db: AsyncSession, category_id: int, include_deleted: bool = False) -> Optional[Category]:
    stmt = select(Category).where(Category.id == category_id)
    stmt = filter_not_deleted(stmt, Category, include_deleted)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_category_with_products(db: AsyncSession, category_id: int, include_deleted: bool = False) -> Optional[Category]:
    stmt = (
        select(Category)
        .options(selectinload(Category.products))
        .where(Category.id == category_id)
    )
    stmt = filter_not_deleted(stmt, Category, include_deleted)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_categories(
    db: AsyncSession,
    params: schemas.CategoryQueryParams
) -> tuple[List[Category], int]:
    stmt = select(Category)
    stmt = filter_not_deleted(stmt, Category, params.include_deleted)
    
    if params.name:
        stmt = stmt.where(Category.name.ilike(f"%{params.name}%"))
    
    count_stmt = select(func.count(Category.id))
    count_stmt = filter_not_deleted(count_stmt, Category, params.include_deleted)
    if params.name:
        count_stmt = count_stmt.where(Category.name.ilike(f"%{params.name}%"))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.offset(params.skip).limit(params.limit)
    result = await db.execute(stmt)
    categories = result.scalars().all()
    
    return list(categories), total


async def get_categories_with_products(
    db: AsyncSession,
    params: schemas.PaginationQueryParams,
    include_deleted: bool = False
) -> tuple[List[Category], int]:
    stmt = select(Category).options(selectinload(Category.products))
    stmt = filter_not_deleted(stmt, Category, include_deleted)
    
    count_stmt = select(func.count(Category.id))
    count_stmt = await filter_not_deleted(count_stmt, Category, include_deleted)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.offset(params.skip).limit(params.limit)
    result = await db.execute(stmt)
    categories = result.scalars().all()
    return list(categories), total


async def soft_delete_category(db: AsyncSession, category_id: int) -> Optional[Category]:
    stmt = select(Category).where(Category.id == category_id, Category.deleted_at.is_(None))
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()
    if not category:
        return None
    
    category.deleted_at = datetime.utcnow()
    await db.commit()
    await db.refresh(category)
    return category


async def restore_category(db: AsyncSession, category_id: int) -> Optional[Category]:
    stmt = select(Category).where(Category.id == category_id, Category.deleted_at.isnot(None))
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()
    if not category:
        return None
    
    category.deleted_at = None
    await db.commit()
    await db.refresh(category)
    return category


async def create_order(
    db: AsyncSession,
    order_data: schemas.OrderCreate
) -> Order:
    stmt = select(User).where(User.id == order_data.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    order = Order(
        user_id=order_data.user_id,
        status=order_data.status
    )
    db.add(order)
    await db.flush()
    
    # Merge duplicate products by summing quantities
    # Use dict to track product_id -> (quantity, price)
    items_dict = {}
    for item_data in order_data.items:
        if item_data.product_id in items_dict:
            # If product already exists, sum quantities (use first price)
            items_dict[item_data.product_id] = (
                items_dict[item_data.product_id][0] + item_data.quantity,
                items_dict[item_data.product_id][1]  # Keep first price
            )
        else:
            items_dict[item_data.product_id] = (item_data.quantity, item_data.price)
    
    # Validate all products exist
    product_ids = list(items_dict.keys())
    stmt = select(Product).where(Product.id.in_(product_ids))
    result = await db.execute(stmt)
    products = result.scalars().all()
    found_product_ids = {p.id for p in products}
    
    missing_ids = set(product_ids) - found_product_ids
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Products with ids {list(missing_ids)} not found"
        )
    
    # Create order items
    for product_id, (quantity, price) in items_dict.items():
        order_item = OrderItem(
            order_id=order.id,
            product_id=product_id,
            quantity=quantity,
            price=price
        )
        db.add(order_item)
    
    await db.commit()
    await db.refresh(order)
    return order


async def get_order(db: AsyncSession, order_id: int, include_deleted: bool = False) -> Optional[Order]:
    stmt = select(Order).where(Order.id == order_id)
    stmt = filter_not_deleted(stmt, Order, include_deleted)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_order_with_items(db: AsyncSession, order_id: int, include_deleted: bool = False) -> Optional[Order]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    stmt = filter_not_deleted(stmt, Order, include_deleted)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_order_with_items_and_products(db: AsyncSession, order_id: int, include_deleted: bool = False) -> Optional[Order]:
    stmt = (
        select(Order)
        .options(
            selectinload(Order.items).joinedload(OrderItem.product)
        )
        .where(Order.id == order_id)
    )
    stmt = filter_not_deleted(stmt, Order, include_deleted)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_order_full(db: AsyncSession, order_id: int, include_deleted: bool = False) -> Optional[Order]:
    stmt = (
        select(Order)
        .options(
            joinedload(Order.user),
            selectinload(Order.items).joinedload(OrderItem.product)
        )
        .where(Order.id == order_id)
    )
    stmt = filter_not_deleted(stmt, Order, include_deleted)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_orders(
    db: AsyncSession,
    params: schemas.OrderQueryParams
) -> tuple[List[Order], int]:
    stmt = select(Order)
    stmt = filter_not_deleted(stmt, Order, params.include_deleted)
    
    if params.user_id is not None:
        stmt = stmt.where(Order.user_id == params.user_id)
    
    if params.status is not None:
        stmt = stmt.where(Order.status == params.status)
    
    count_stmt = select(func.count(Order.id))
    count_stmt = filter_not_deleted(count_stmt, Order, params.include_deleted)
    if params.user_id is not None:
        count_stmt = count_stmt.where(Order.user_id == params.user_id)
    if params.status is not None:
        count_stmt = count_stmt.where(Order.status == params.status)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.order_by(Order.created_at.desc()).offset(params.skip).limit(params.limit)
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    return list(orders), total


async def get_orders_with_items(
    db: AsyncSession,
    params: schemas.PaginationQueryParams,
    include_deleted: bool = False
) -> tuple[List[Order], int]:
    stmt = select(Order).options(selectinload(Order.items))
    stmt = filter_not_deleted(stmt, Order, include_deleted)
    
    count_stmt = select(func.count(Order.id))
    count_stmt = await filter_not_deleted(count_stmt, Order, include_deleted)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.order_by(Order.created_at.desc()).offset(params.skip).limit(params.limit)
    result = await db.execute(stmt)
    orders = result.scalars().all()
    return list(orders), total


async def get_orders_with_items_and_products(
    db: AsyncSession,
    params: schemas.PaginationQueryParams,
    include_deleted: bool = False
) -> tuple[List[Order], int]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items).joinedload(OrderItem.product))
    )
    stmt = filter_not_deleted(stmt, Order, include_deleted)
    
    count_stmt = select(func.count(Order.id))
    count_stmt = await filter_not_deleted(count_stmt, Order, include_deleted)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.order_by(Order.created_at.desc()).offset(params.skip).limit(params.limit)
    result = await db.execute(stmt)
    orders = result.scalars().all()
    return list(orders), total


async def update_order(
    db: AsyncSession,
    order_id: int,
    order_update: schemas.OrderUpdate
) -> Optional[Order]:
    stmt = select(Order).where(Order.id == order_id, Order.deleted_at.is_(None))
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    if not order:
        return None
    
    update_data = order_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    await db.commit()
    await db.refresh(order)
    return order


async def soft_delete_order(db: AsyncSession, order_id: int) -> Optional[Order]:
    stmt = select(Order).where(Order.id == order_id, Order.deleted_at.is_(None))
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    if not order:
        return None
    
    order.deleted_at = datetime.utcnow()
    await db.commit()
    await db.refresh(order)
    return order


async def restore_order(db: AsyncSession, order_id: int) -> Optional[Order]:
    stmt = select(Order).where(Order.id == order_id, Order.deleted_at.isnot(None))
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    if not order:
        return None
    
    order.deleted_at = None
    await db.commit()
    await db.refresh(order)
    return order


async def get_user_orders(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    include_deleted: bool = False
) -> tuple[List[Order], int]:
    stmt = select(Order).where(Order.user_id == user_id)
    stmt = filter_not_deleted(stmt, Order, include_deleted)
    
    count_stmt = select(func.count(Order.id)).where(Order.user_id == user_id)
    count_stmt = await filter_not_deleted(count_stmt, Order, include_deleted)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    orders = result.scalars().all()
    return list(orders), total


async def get_product_orders(
    db: AsyncSession,
    product_id: int,
    skip: int = 0,
    limit: int = 10,
    include_deleted: bool = False
) -> tuple[List[Order], int]:
    stmt = (
        select(Order)
        .join(OrderItem)
        .where(OrderItem.product_id == product_id)
    )
    stmt = filter_not_deleted(stmt, Order, include_deleted)
    
    count_stmt = (
        select(func.count(Order.id))
        .join(OrderItem)
        .where(OrderItem.product_id == product_id)
    )
    count_stmt = await filter_not_deleted(count_stmt, Order, include_deleted)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    orders = result.scalars().all()
    return list(orders), total
