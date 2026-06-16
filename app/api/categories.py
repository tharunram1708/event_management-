from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.exceptions import ConflictError, NotFoundError
from app.db.session import get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.common import Message

router = APIRouter(prefix="/categories", tags=["Event Categories"])


@router.post("", response_model=CategoryRead, status_code=201)
def create_category(
    payload: CategoryCreate,
    _: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> Category:
    if db.scalar(select(Category).where(Category.name == payload.name)):
        raise ConflictError("Category already exists")
    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)))


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    _: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError("Category not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", response_model=Message)
def delete_category(
    category_id: int,
    _: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> Message:
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError("Category not found")
    db.delete(category)
    db.commit()
    return Message(message="Category deleted")
