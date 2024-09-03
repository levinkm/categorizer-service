
import pandas as pd
from typing import  Dict, List
from src.database.db_utils import TransactionService
from src.models.models import Transaction
from src.utils.utils import loader
from src.utils.logging_utils import setup_logger

logger = setup_logger(name=__name__)

def load_keyword_categories() -> Dict[str, List[str]]:
    """Load keyword-based categories from a data source."""
    return loader._load_keyword_categories()

def load_merchant_categories() -> Dict[str, str]:
    """Load merchant-based categories from a data source."""
    return loader._load_merchant_categories()

def load_training_data(transactionDB: TransactionService) -> pd.DataFrame:
    """Load training data for the model from the transaction database."""
    try:
        transactions: List[Transaction] = transactionDB.get_latest_transactions_with_category(2000)
   
        df = pd.DataFrame([
            {
                'transaction_id': t.id,
                'type': t.type,
                'amount': t.amount,
                'narration': t.narration,
                'date': t.date,
                'category_id': t.category_id,
                'subcategory_id': t.subcategory_id,
                'currency': t.currency
            } for t in transactions
        ])
    
        # Ensure 'date' is in datetime format
        df['date'] = pd.to_datetime(df['date'])
    
        return df
    except Exception as e:
        logger.error(f"Error loading training data: {str(e)}")
        raise