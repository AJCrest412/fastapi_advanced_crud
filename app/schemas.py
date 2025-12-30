from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============ User Schemas ============
class UserCreate(BaseModel):
    email: str = Field(..., description="User email address")


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserWithProducts(BaseModel):
    """User with nested products (one-to-many relationship)"""
    id: int
    email: str
    created_at: datetime
    products: List["ProductNested"] = []

    class Config:
        from_attributes = True


# ============ Category Schemas ============
class CategoryCreate(BaseModel):
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CategoryNested(BaseModel):
    """Simplified category for nesting in products"""
    id: int
    name: str

    class Config:
        from_attributes = True


class CategoryWithProducts(BaseModel):
    """Category with nested products (many-to-many relationship)"""
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    products: List["ProductNested"] = []

    class Config:
        from_attributes = True


# ============ Product Schemas ============
class ProductCreate(BaseModel):
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: Optional[float] = Field(None, ge=0, description="Product price")
    owner_id: int = Field(..., description="ID of the user who owns this product")
    category_ids: Optional[List[int]] = Field(default=[], description="List of category IDs")


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    category_ids: Optional[List[int]] = None


class ProductNested(BaseModel):
    """Simplified product for nesting in users/categories"""
    id: int
    name: str
    price: Optional[float]
    is_active: bool

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    """Basic product response"""
    id: int
    name: str
    description: Optional[str]
    price: Optional[float]
    is_active: bool
    owner_id: int
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductWithOwner(BaseModel):
    """Product with nested owner (many-to-one relationship)"""
    id: int
    name: str
    description: Optional[str]
    price: Optional[float]
    is_active: bool
    owner_id: int
    created_at: datetime
    owner: UserResponse

    class Config:
        from_attributes = True


class ProductWithCategories(BaseModel):
    """Product with nested categories (many-to-many relationship)"""
    id: int
    name: str
    description: Optional[str]
    price: Optional[float]
    is_active: bool
    owner_id: int
    created_at: datetime
    categories: List[CategoryNested] = []

    class Config:
        from_attributes = True


class ProductFull(BaseModel):
    """Product with both owner and categories (complete relationship)"""
    id: int
    name: str
    description: Optional[str]
    price: Optional[float]
    is_active: bool
    owner_id: int
    created_at: datetime
    owner: UserResponse
    categories: List[CategoryNested] = []

    class Config:
        from_attributes = True


# ============ Pagination Schemas ============
class PaginationParams(BaseModel):
    """Query parameters for pagination"""
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of records to return")


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    total: int
    skip: int
    limit: int
    count: int


class PaginatedProducts(PaginatedResponse):
    """Paginated products response"""
    items: List[ProductResponse]


class PaginatedUsers(PaginatedResponse):
    """Paginated users response"""
    items: List[UserResponse]


class PaginatedCategories(PaginatedResponse):
    """Paginated categories response"""
    items: List[CategoryResponse]


# ============ Query Parameter Schemas (for endpoints with many query params) ============
# These schemas combine pagination + filters for cleaner endpoint signatures
# Use these with Depends() to avoid having 8+ individual query parameters

class PaginationQueryParams(BaseModel):
    """Common pagination parameters for query strings"""
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of records to return")


class ProductQueryParams(PaginationQueryParams):
    """
    Query parameters for listing products.
    
    This combines pagination + filters in one schema, making endpoints much cleaner.
    Instead of 8+ individual parameters, we have one clean schema object.
    Use with Depends() in the endpoint.
    """
    name: Optional[str] = Field(None, description="Filter by product name (partial match)")
    owner_id: Optional[int] = Field(None, description="Filter by owner ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    category_id: Optional[int] = Field(None, description="Filter by category ID")
    include_deleted: bool = Field(False, description="Include soft-deleted products")


class UserQueryParams(PaginationQueryParams):
    """Query parameters for listing users"""
    email: Optional[str] = Field(None, description="Filter by email (partial match)")
    include_deleted: bool = Field(False, description="Include soft-deleted users")


class CategoryQueryParams(PaginationQueryParams):
    """Query parameters for listing categories"""
    name: Optional[str] = Field(None, description="Filter by category name (partial match)")
    include_deleted: bool = Field(False, description="Include soft-deleted categories")


class OrderQueryParams(PaginationQueryParams):
    """Query parameters for listing orders"""
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    status: Optional[str] = Field(None, description="Filter by order status")
    include_deleted: bool = Field(False, description="Include soft-deleted orders")


# ============ Filter Schemas (kept for backward compatibility if needed) ============
class ProductFilter(BaseModel):
    """Filter parameters for products (legacy - use ProductQueryParams instead)"""
    name: Optional[str] = Field(None, description="Filter by product name (partial match)")
    owner_id: Optional[int] = Field(None, description="Filter by owner ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    category_id: Optional[int] = Field(None, description="Filter by category ID")


class UserFilter(BaseModel):
    """Filter parameters for users (legacy - use UserQueryParams instead)"""
    email: Optional[str] = Field(None, description="Filter by email (partial match)")


class CategoryFilter(BaseModel):
    """Filter parameters for categories (legacy - use CategoryQueryParams instead)"""
    name: Optional[str] = Field(None, description="Filter by category name (partial match)")


# ============ OrderItem Schemas ============
class OrderItemCreate(BaseModel):
    """Create an order item"""
    product_id: int = Field(..., description="ID of the product")
    quantity: int = Field(..., gt=0, description="Quantity of the product")
    price: float = Field(..., ge=0, description="Price per unit at time of order")


class OrderItemResponse(BaseModel):
    """Order item response"""
    order_id: int
    product_id: int
    quantity: int
    price: float

    class Config:
        from_attributes = True


class OrderItemWithProduct(BaseModel):
    """Order item with nested product information"""
    order_id: int
    product_id: int
    quantity: int
    price: float
    product: ProductNested

    class Config:
        from_attributes = True


# ============ Order Schemas ============
class OrderCreate(BaseModel):
    """Create an order with items"""
    user_id: int = Field(..., description="ID of the user placing the order")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="List of order items")
    status: Optional[str] = Field("pending", description="Order status (pending, completed, cancelled)")


class OrderUpdate(BaseModel):
    """Update an order"""
    status: Optional[str] = Field(None, description="Order status (pending, completed, cancelled)")


class OrderResponse(BaseModel):
    """Basic order response"""
    id: int
    user_id: int
    status: str
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderWithItems(BaseModel):
    """Order with nested order items (one-to-many relationship)"""
    id: int
    user_id: int
    status: str
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True


class OrderWithItemsAndProducts(BaseModel):
    """Order with items and product details (many-to-many through association object)"""
    id: int
    user_id: int
    status: str
    created_at: datetime
    items: List[OrderItemWithProduct] = []

    class Config:
        from_attributes = True


class OrderFull(BaseModel):
    """Order with user, items, and product details (all relationships)"""
    id: int
    user_id: int
    status: str
    created_at: datetime
    user: UserResponse
    items: List[OrderItemWithProduct] = []

    class Config:
        from_attributes = True


class PaginatedOrders(PaginatedResponse):
    """Paginated orders response"""
    items: List[OrderResponse]


# ============ Filter Schemas for Orders ============
class OrderFilter(BaseModel):
    """Filter parameters for orders"""
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    status: Optional[str] = Field(None, description="Filter by order status")


# Rebuild models to resolve forward references (Pydantic v2)
UserWithProducts.model_rebuild()
CategoryWithProducts.model_rebuild()
ProductWithCategories.model_rebuild()
ProductFull.model_rebuild()
OrderWithItems.model_rebuild()
OrderWithItemsAndProducts.model_rebuild()
OrderItemWithProduct.model_rebuild()
OrderFull.model_rebuild()