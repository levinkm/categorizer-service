from datetime import date, datetime, timedelta
from math import log
from operator import or_
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from .db_connector import get_db

from src.models.models import Category, Transaction
from src.utils.logging_utils import setup_logger

logger = setup_logger(__name__)

class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    def get_transaction(self, transaction_id: int):
        try:
            transaction = self.db.query(Transaction).filter(Transaction.transaction_id == transaction_id).one()
            return transaction
        except NoResultFound:
            return None

    def get_transactions_by_user(self, user_id: int):
        transactions = self.db.query(Transaction).filter(Transaction.user_id == user_id).all()
        return transactions

    def update_transaction(self, transaction_id: int, update_data: dict) -> bool:
        try:
           
            transaction = self.db.query(Transaction).filter(Transaction.id == transaction_id).with_for_update().first()
            
            if not transaction:
                logger.warning(f"Transaction {transaction_id} not found.")
                return False
            
            for key, value in update_data.items():
                setattr(transaction, key, value)
            
            self.db.commit()
            return True
        except IntegrityError:

            self.db.rollback()
            logger.warning(f"IntegrityError: Transaction {transaction_id} may already be updated.")
            return False
        except Exception as e:
            
            self.db.rollback()
            logger.error(f"Error updating transaction {transaction_id}: {str(e)}")
            return False


    def get_latest_transactions_with_category(self, limit: int = 1000):
        transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.category_id.isnot(None),
                Transaction.category_id != 32
            )
            .order_by(desc(Transaction.date))
            .limit(limit)
            .all()
        )
        return transactions
    
    def get_transactions_last_24hrs_with_category(self, limit: int = 1000):
    # Get the current time and the time 24 hours ago
        now = datetime.now()
        last_24hrs = now - timedelta(hours=24)
        
        transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.category_id.isnot(None),
                Transaction.category_id != 32,
                Transaction.date >= last_24hrs
            )
            .order_by(desc(Transaction.date))
            .limit(limit)
            .all()
        )
        
        return transactions

    
    def get_latest_transactions_with_no_category(self, limit: int = 1000):
        transactions = (
            self.db.query(Transaction)
            .filter(
                or_(
                    Transaction.category_id.is_(None),
                    Transaction.category_id == 32
                )
            )
            .order_by(desc(Transaction.date))
            .limit(limit)
            .all()
        )
        return transactions
    
    def get_transaction_id_by_description(self, description: str):
        # Use the LIKE operator for partial matches
        transactions = self.db.query(Transaction).filter(
            or_(
                Transaction.description.like(f"%{description}%"),
                Transaction.note.like(f"%{description}%")
            )
        ).all()

        if not transactions:
            return None
        
        # Optionally, return the most similar transaction or a list of potential matches
        return transactions[0].transaction_id if transactions else None

class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_category(self, category_id: int):
        try:
            category = self.db.query(Category).filter(Category.id == category_id).one()
            return category
        except NoResultFound:
            return None
    def get_category_by_name(self, category_name: str)-> Optional[Category]:
        try:
            category = self.db.query(Category).filter(
                Category.name.like(f"%{category_name}%")
            ).one_or_none()
            logger.info(f"Found category: {category} using {category_name}")
            return category
        except NoResultFound:

            return None

def get_transaction_service() -> CategoryService:
    db = next(get_db())
    return TransactionService(db=db)

def get_category_service() -> CategoryService:
    db = next(get_db())
    return CategoryService(db=db)


# print(get_category_service().get_category(7))


