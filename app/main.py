from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app import crud, schemas


def get_product_query_params(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None),
    owner_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    category_id: Optional[int] = Query(None),
    include_deleted: bool = Query(False)
) -> schemas.ProductQueryParams:
    return schemas.ProductQueryParams(
        skip=skip,
        limit=limit,
        name=name,
        owner_id=owner_id,
        is_active=is_active,
        min_price=min_price,
        max_price=max_price,
        category_id=category_id,
        include_deleted=include_deleted
    )


def get_user_query_params(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    email: Optional[str] = Query(None),
    include_deleted: bool = Query(False)
) -> schemas.UserQueryParams:
    return schemas.UserQueryParams(
        skip=skip,
        limit=limit,
        email=email,
        include_deleted=include_deleted
    )


def get_order_query_params(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    include_deleted: bool = Query(False)
) -> schemas.OrderQueryParams:
    return schemas.OrderQueryParams(
        skip=skip,
        limit=limit,
        user_id=user_id,
        status=status,
        include_deleted=include_deleted
    )


def get_category_query_params(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None),
    include_deleted: bool = Query(False)
) -> schemas.CategoryQueryParams:
    return schemas.CategoryQueryParams(
        skip=skip,
        limit=limit,
        name=name,
        include_deleted=include_deleted
    )


def get_pagination_params(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
) -> schemas.PaginationQueryParams:
    return schemas.PaginationQueryParams(
        skip=skip,
        limit=limit
    )

app = FastAPI(
    title="FastAPI ORM Relationships Demo",
    description="Demonstrates SQLAlchemy relationships, filters, and pagination",
    version="1.0.0"
)


@app.post("/users", response_model=schemas.UserResponse, status_code=201, tags=["Users"])
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    return crud.create_user(db, user_data=user)


@app.get("/users", response_model=schemas.PaginatedUsers, tags=["Users"])
def list_users(
    params: schemas.UserQueryParams = Depends(get_user_query_params),
    db: Session = Depends(get_db)
):
    users, total = crud.get_users(db, params)
    return {
        "items": users,
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
        "count": len(users)
    }


@app.get("/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/{user_id}/with-products", response_model=schemas.UserWithProducts, tags=["Users"])
def get_user_with_products(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user_with_products(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/with-products/all", response_model=schemas.PaginatedUsers, tags=["Users"])
def list_users_with_products(
    params: schemas.PaginationQueryParams = Depends(get_pagination_params),
    db: Session = Depends(get_db)
):
    users, total = crud.get_users_with_products(db, params)
    return {
        "items": users,
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
        "count": len(users)
    }


@app.post("/products", response_model=schemas.ProductResponse, status_code=201, tags=["Products"])
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db)
):
    return crud.create_product(db, product_data=product)


@app.get("/products", response_model=schemas.PaginatedProducts, tags=["Products"])
def list_products(
    params: schemas.ProductQueryParams = Depends(get_product_query_params),
    db: Session = Depends(get_db)
):
    products, total = crud.get_products(db, params)
    return {
        "items": products,
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
        "count": len(products)
    }


@app.get("/products/{product_id}", response_model=schemas.ProductResponse, tags=["Products"])
def get_product(
    product_id: int,
    include_deleted: bool = Query(False, description="Include soft-deleted product"),
    db: Session = Depends(get_db)
):
    product = crud.get_product(db, product_id, include_deleted=include_deleted)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/products/{product_id}/with-owner", response_model=schemas.ProductWithOwner, tags=["Products"])
def get_product_with_owner(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product_with_owner(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/products/{product_id}/with-categories", response_model=schemas.ProductWithCategories, tags=["Products"])
def get_product_with_categories(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product_with_categories(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/products/{product_id}/full", response_model=schemas.ProductFull, tags=["Products"])
def get_product_full(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product_full(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/products/with-owner/all", response_model=schemas.PaginatedProducts, tags=["Products"])
def list_products_with_owner(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    products, total = crud.get_products_with_owner(db, skip=skip, limit=limit)
    return {
        "items": products,
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(products)
    }


@app.get("/products/with-categories/all", response_model=schemas.PaginatedProducts, tags=["Products"])
def list_products_with_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    products, total = crud.get_products_with_categories(db, skip=skip, limit=limit)
    return {
        "items": products,
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(products)
    }


@app.put("/products/{product_id}", response_model=schemas.ProductResponse, tags=["Products"])
def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    db: Session = Depends(get_db)
):
    product = crud.update_product(db, product_id, product_update=product_update)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.delete("/products/{product_id}", response_model=schemas.ProductResponse, tags=["Products"])
def soft_delete_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.soft_delete_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or already deleted")
    return product


@app.post("/products/{product_id}/restore", response_model=schemas.ProductResponse, tags=["Products"])
def restore_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.restore_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not deleted")
    return product


@app.post("/categories", response_model=schemas.CategoryResponse, status_code=201, tags=["Categories"])
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db)
):
    return crud.create_category(db, category_data=category)


@app.get("/categories", response_model=schemas.PaginatedCategories, tags=["Categories"])
def list_categories(
    params: schemas.CategoryQueryParams = Depends(get_category_query_params),
    db: Session = Depends(get_db)
):
    categories, total = crud.get_categories(db, params)
    return {
        "items": categories,
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
        "count": len(categories)
    }


@app.get("/categories/{category_id}", response_model=schemas.CategoryResponse, tags=["Categories"])
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = crud.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@app.get("/categories/{category_id}/with-products", response_model=schemas.CategoryWithProducts, tags=["Categories"])
def get_category_with_products(category_id: int, db: Session = Depends(get_db)):
    category = crud.get_category_with_products(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@app.get("/categories/with-products/all", response_model=schemas.PaginatedCategories, tags=["Categories"])
def list_categories_with_products(
    params: schemas.PaginationQueryParams = Depends(get_pagination_params),
    db: Session = Depends(get_db)
):
    categories, total = crud.get_categories_with_products(db, params)
    return {
        "items": categories,
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
        "count": len(categories)
    }


@app.post("/orders", response_model=schemas.OrderResponse, status_code=201, tags=["Orders"])
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db)
):
    return crud.create_order(db, order_data=order)


@app.get("/orders", response_model=schemas.PaginatedOrders, tags=["Orders"])
def list_orders(
    params: schemas.OrderQueryParams = Depends(get_order_query_params),
    db: Session = Depends(get_db)
):
    orders, total = crud.get_orders(db, params)
    return {
        "items": orders,
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
        "count": len(orders)
    }


@app.get("/orders/{order_id}", response_model=schemas.OrderResponse, tags=["Orders"])
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/orders/{order_id}/with-items", response_model=schemas.OrderWithItems, tags=["Orders"])
def get_order_with_items(order_id: int, db: Session = Depends(get_db)):
    order = crud.get_order_with_items(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/orders/{order_id}/with-items-and-products", response_model=schemas.OrderWithItemsAndProducts, tags=["Orders"])
def get_order_with_items_and_products(order_id: int, db: Session = Depends(get_db)):
    order = crud.get_order_with_items_and_products(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/orders/{order_id}/full", response_model=schemas.OrderFull, tags=["Orders"])
def get_order_full(order_id: int, db: Session = Depends(get_db)):
    order = crud.get_order_full(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/orders/with-items/all", response_model=schemas.PaginatedOrders, tags=["Orders"])
def list_orders_with_items(
    params: schemas.PaginationQueryParams = Depends(get_pagination_params),
    db: Session = Depends(get_db)
):
    orders, total = crud.get_orders_with_items(db, params)
    return {
        "items": orders,
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
        "count": len(orders)
    }


@app.get("/orders/with-items-and-products/all", response_model=schemas.PaginatedOrders, tags=["Orders"])
def list_orders_with_items_and_products(
    params: schemas.PaginationQueryParams = Depends(get_pagination_params),
    db: Session = Depends(get_db)
):
    orders, total = crud.get_orders_with_items_and_products(db, params)
    return {
        "items": orders,
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
        "count": len(orders)
    }


@app.put("/orders/{order_id}", response_model=schemas.OrderResponse, tags=["Orders"])
def update_order(
    order_id: int,
    order_update: schemas.OrderUpdate,
    db: Session = Depends(get_db)
):
    order = crud.update_order(db, order_id, order_update=order_update)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.delete("/orders/{order_id}", response_model=schemas.OrderResponse, tags=["Orders"])
def soft_delete_order(order_id: int, db: Session = Depends(get_db)):
    order = crud.soft_delete_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or already deleted")
    return order


@app.post("/orders/{order_id}/restore", response_model=schemas.OrderResponse, tags=["Orders"])
def restore_order(order_id: int, db: Session = Depends(get_db)):
    order = crud.restore_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or not deleted")
    return order


@app.get("/users/{user_id}/orders", response_model=schemas.PaginatedOrders, tags=["Users", "Orders"])
def get_user_orders(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    orders, total = crud.get_user_orders(db, user_id, skip=skip, limit=limit)
    return {
        "items": orders,
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(orders)
    }


@app.get("/products/{product_id}/orders", response_model=schemas.PaginatedOrders, tags=["Products", "Orders"])
def get_product_orders(
    product_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    orders, total = crud.get_product_orders(db, product_id, skip=skip, limit=limit)
    return {
        "items": orders,
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(orders)
    }


# ============ ROOT ENDPOINT ============

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "FastAPI ORM Relationships Demo",
        "docs": "/docs",
        "relationships": {
            "one_to_many": [
                "User -> Products (one user has many products)",
                "User -> Orders (one user has many orders)",
                "Order -> OrderItems (one order has many order items)"
            ],
            "many_to_many": [
                "Products <-> Categories (simple association table)",
                "Orders <-> Products (through OrderItem association object with quantity and price)"
            ],
            "many_to_one": [
                "Product -> User (many products belong to one user)",
                "Order -> User (many orders belong to one user)",
                "OrderItem -> Order (many order items belong to one order)",
                "OrderItem -> Product (many order items reference one product)"
            ]
        },
        "features": [
            "Filtering by various fields",
            "Pagination with skip/limit",
            "Eager loading to prevent N+1 queries",
            "Nested relationship responses",
            "Association object pattern (OrderItem with additional attributes)"
        ]
    }