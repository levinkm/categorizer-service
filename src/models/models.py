from sqlalchemy import Column, BigInteger, SmallInteger, String, Text, Integer, DateTime, Enum, ForeignKey, func, Boolean, TIMESTAMP, text
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import relationship

from src.database.db_connector import Base

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # user_id = Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    transaction_id = Column(String(254), nullable=False, unique=True, index=True)
    category_id = Column(BigInteger, ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True)
    subcategory_id = Column(BigInteger, ForeignKey('subcategories.id', ondelete='SET NULL'), nullable=True, index=True)
    # wallet_id = Column(BigInteger, ForeignKey('wallets.id', ondelete='SET NULL'), nullable=True)
    type = Column(Enum('credit', 'debit', name='transaction_type'), nullable=False)
    amount = Column(BigInteger, nullable=False)
    narration = Column(Text, nullable=False)
    date = Column(DateTime, nullable=True, index=True)
    balance = Column(BigInteger, nullable=False)
    charges = Column(Integer, nullable=False, default=0)
    currency = Column(VARCHAR(5), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(),server_default=func.now(), server_onupdate=func.now(), nullable=False)

    category = relationship("Category", back_populates="transactions", lazy="joined")

    def __repr__(self):
        return f"<Transaction(id={self.id}, transaction_id='{self.transaction_id}', amount={self.amount})>"
    
class Category(Base):
    __tablename__ = 'categories'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    name = Column(String(255), nullable=False)
    image = Column(String(255), nullable=True)
    status = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now(), nullable=False)

    transactions = relationship("Transaction", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

class Subcategory(Base):
    __tablename__ = 'subcategories'

    id = Column(BigInteger, primary_key=True)
    name = Column(String(255, collation='utf8mb4_unicode_ci'), nullable=False)
    category_id = Column(BigInteger, nullable=False)
    image = Column(String(255, collation='utf8mb4_unicode_ci'), nullable=True)
    status = Column(SmallInteger, nullable=False, default=1)
    created_at = Column(TIMESTAMP, nullable=True, default=None)
    updated_at = Column(TIMESTAMP, nullable=True, default=None, onupdate=text('CURRENT_TIMESTAMP'))

    def __repr__(self):
        return f"<Subcategory(id={self.id}, name='{self.name}', category_id={self.category_id})>"