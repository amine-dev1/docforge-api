from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_enterprise, SecurityContext
from app.models.catalogue import UnitOfMeasure, TaxRate, ProductCategory, Product
from app.schemas.catalogue import (
    UnitOfMeasureCreate, UnitOfMeasureUpdate, UnitOfMeasureOut,
    TaxRateCreate, TaxRateUpdate, TaxRateOut,
    ProductCategoryCreate, ProductCategoryUpdate, ProductCategoryOut,
    ProductCreate, ProductUpdate, ProductOut,
)
from app.schemas.response import StandardResponse

router = APIRouter(tags=["Catalogue"])


# ─────────────────────────────────────────────
# UNITS OF MEASURE
# ─────────────────────────────────────────────

uom_router = APIRouter(prefix="/catalogue/units", tags=["Catalogue"])

@uom_router.get("/", response_model=StandardResponse[List[UnitOfMeasureOut]])
async def list_units(
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    units = db.query(UnitOfMeasure).filter(UnitOfMeasure.enterprise_id == ctx.enterprise.id).all()
    return {"status": 200, "data": units}


@uom_router.post("/", response_model=StandardResponse[UnitOfMeasureOut], status_code=status.HTTP_201_CREATED)
async def create_unit(
    unit_in: UnitOfMeasureCreate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    unit = UnitOfMeasure(**unit_in.model_dump(), enterprise_id=ctx.enterprise.id)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return {"status": 201, "data": unit}


@uom_router.patch("/{unit_id}", response_model=StandardResponse[UnitOfMeasureOut])
async def update_unit(
    unit_id: UUID,
    unit_in: UnitOfMeasureUpdate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    unit = db.query(UnitOfMeasure).filter(
        UnitOfMeasure.id == unit_id,
        UnitOfMeasure.enterprise_id == ctx.enterprise.id
    ).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    for field, value in unit_in.model_dump(exclude_none=True).items():
        setattr(unit, field, value)
    db.commit()
    db.refresh(unit)
    return {"status": 200, "data": unit}


@uom_router.delete("/{unit_id}", response_model=StandardResponse[dict])
async def delete_unit(
    unit_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    unit = db.query(UnitOfMeasure).filter(
        UnitOfMeasure.id == unit_id,
        UnitOfMeasure.enterprise_id == ctx.enterprise.id
    ).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    db.delete(unit)
    db.commit()
    return {"status": 200, "data": {"message": "Unit deleted"}}


# ─────────────────────────────────────────────
# TAX RATES
# ─────────────────────────────────────────────

tax_router = APIRouter(prefix="/catalogue/tax-rates", tags=["Catalogue"])

@tax_router.get("/", response_model=StandardResponse[List[TaxRateOut]])
async def list_tax_rates(
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    rates = db.query(TaxRate).filter(TaxRate.enterprise_id == ctx.enterprise.id).all()
    return {"status": 200, "data": rates}


@tax_router.post("/", response_model=StandardResponse[TaxRateOut], status_code=status.HTTP_201_CREATED)
async def create_tax_rate(
    rate_in: TaxRateCreate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    rate = TaxRate(**rate_in.model_dump(), enterprise_id=ctx.enterprise.id)
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return {"status": 201, "data": rate}


@tax_router.patch("/{rate_id}", response_model=StandardResponse[TaxRateOut])
async def update_tax_rate(
    rate_id: UUID,
    rate_in: TaxRateUpdate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    rate = db.query(TaxRate).filter(
        TaxRate.id == rate_id,
        TaxRate.enterprise_id == ctx.enterprise.id
    ).first()
    if not rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    for field, value in rate_in.model_dump(exclude_none=True).items():
        setattr(rate, field, value)
    db.commit()
    db.refresh(rate)
    return {"status": 200, "data": rate}


@tax_router.delete("/{rate_id}", response_model=StandardResponse[dict])
async def delete_tax_rate(
    rate_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    rate = db.query(TaxRate).filter(
        TaxRate.id == rate_id,
        TaxRate.enterprise_id == ctx.enterprise.id
    ).first()
    if not rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    db.delete(rate)
    db.commit()
    return {"status": 200, "data": {"message": "Tax rate deleted"}}


# ─────────────────────────────────────────────
# PRODUCT CATEGORIES
# ─────────────────────────────────────────────

cat_router = APIRouter(prefix="/catalogue/categories", tags=["Catalogue"])

@cat_router.get("/", response_model=StandardResponse[List[ProductCategoryOut]])
async def list_categories(
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    cats = db.query(ProductCategory).filter(ProductCategory.enterprise_id == ctx.enterprise.id).all()
    return {"status": 200, "data": cats}


@cat_router.post("/", response_model=StandardResponse[ProductCategoryOut], status_code=status.HTTP_201_CREATED)
async def create_category(
    cat_in: ProductCategoryCreate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    cat = ProductCategory(**cat_in.model_dump(), enterprise_id=ctx.enterprise.id)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return {"status": 201, "data": cat}


@cat_router.patch("/{cat_id}", response_model=StandardResponse[ProductCategoryOut])
async def update_category(
    cat_id: UUID,
    cat_in: ProductCategoryUpdate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    cat = db.query(ProductCategory).filter(
        ProductCategory.id == cat_id,
        ProductCategory.enterprise_id == ctx.enterprise.id
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in cat_in.model_dump(exclude_none=True).items():
        setattr(cat, field, value)
    db.commit()
    db.refresh(cat)
    return {"status": 200, "data": cat}


@cat_router.delete("/{cat_id}", response_model=StandardResponse[dict])
async def delete_category(
    cat_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    cat = db.query(ProductCategory).filter(
        ProductCategory.id == cat_id,
        ProductCategory.enterprise_id == ctx.enterprise.id
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
    return {"status": 200, "data": {"message": "Category deleted"}}


# ─────────────────────────────────────────────
# PRODUCTS
# ─────────────────────────────────────────────

product_router = APIRouter(prefix="/catalogue/products", tags=["Catalogue"])

@product_router.get("/", response_model=StandardResponse[List[ProductOut]])
async def list_products(
    page: int = 1,
    size: int = 20,
    is_active: bool = None,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    query = db.query(Product).filter(Product.enterprise_id == ctx.enterprise.id)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    products = query.offset((page - 1) * size).limit(size).all()
    return {"status": 200, "data": products}


@product_router.post("/", response_model=StandardResponse[ProductOut], status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    product = Product(**product_in.model_dump(), enterprise_id=ctx.enterprise.id, created_by=ctx.user.id)
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"status": 201, "data": product}


@product_router.get("/{product_id}", response_model=StandardResponse[ProductOut])
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.enterprise_id == ctx.enterprise.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"status": 200, "data": product}


@product_router.patch("/{product_id}", response_model=StandardResponse[ProductOut])
async def update_product(
    product_id: UUID,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.enterprise_id == ctx.enterprise.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in product_in.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return {"status": 200, "data": product}


@product_router.delete("/{product_id}", response_model=StandardResponse[dict])
async def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.enterprise_id == ctx.enterprise.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    db.commit()
    return {"status": 200, "data": {"message": f"Product '{product.name}' deactivated"}}


# Merge all sub-routers into the main catalogue router
router.include_router(uom_router)
router.include_router(tax_router)
router.include_router(cat_router)
router.include_router(product_router)
