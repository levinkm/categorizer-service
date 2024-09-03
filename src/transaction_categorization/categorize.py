from venv import logger
import joblib
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from src.transaction_categorization.data_loader import load_keyword_categories, load_merchant_categories
from src.transaction_categorization.model_trainer import load_or_train_model, update_model
from src.utils.logging_utils import setup_logger
from src.database.db_utils import get_transaction_service
from src.transaction_categorization.categorization_rules import (
    match_by_keyword, 
    match_by_merchant, 
    categorize_by_ml,
    # categorize_by_amount, 
    # categorize_by_date,
    )
from src.utils.config_utils import config


class EnhancedTransactionCategorizationService:
    """
    A service for categorizing financial transactions using multiple methods including
    keyword matching, merchant matching, machine learning, and rule-based categorization.
    """

    def __init__(self, model_path: str = 'transaction_categorization_model.joblib'):
        """
        Initialize the transaction categorization service.

        Args:
            model_path (str): Path to the saved machine learning model.
        """
        self.logger = setup_logger(__name__)
        self.keyword_categories = load_keyword_categories()
        self.merchant_categories = load_merchant_categories()
        self.model_path = model_path
        self.transactionDB = get_transaction_service()
        self.ml_model = load_or_train_model(model_path, self.logger,self.transactionDB)

        logger.info(self.keyword_categories)

    def categorize_transaction(self, narration: str, amount: float, date: Optional[datetime] = None) -> str:
        """
        Categorize a single transaction using multiple methods.

        Args:
            narration (str): The transaction description.
            amount (float): The transaction amount.
            date (datetime, optional): The transaction date.

        Returns:
            str: The assigned category.
        """
        # Define the list of categorizer functions
        categorizers = [
            lambda n, a, d: match_by_keyword(n, self.keyword_categories),
            lambda n, a, d: match_by_merchant(n, self.merchant_categories),
        ]
        
        # Conditionally add the model-based categorizer if the flag is set
        if config["features"]["categorise_with_model"]:
            categorizers.append(lambda n, a, d: categorize_by_ml(n, a, self.ml_model))
        
        # Process each categorizer function
        for categorizer in categorizers:
            category = categorizer(narration, amount, date)
            if category:
                return category
        
        return 'unknown'

    def update_model(self, new_data: pd.DataFrame) -> None:
        """
        Update the model with new training data.

        Args:
            new_data (pd.DataFrame): New training data to update the model.
        """
        self.ml_model = update_model(self.ml_model, new_data, self.model_path, self.logger)

    def batch_categorize(self, transactions: List[Dict]) -> List[Tuple[Dict, str]]:
        """
        Categorize a batch of transactions.

        Args:
            transactions (List[Dict]): A list of transaction dictionaries.

        Returns:
            List[Tuple[Dict, str]]: A list of tuples containing the original transaction and its category.
        """
        return [(transaction, self.categorize_transaction(
            transaction['narration'],
            transaction['amount'],
            transaction.get('date')
        )) for transaction in transactions]
    
    def save_model(self):
        joblib.dump(self.ml_model, self.model_path)
        self.logger.info(f"Model saved to {self.model_path}")

    def load_model(self):
        self.ml_model = joblib.load(self.model_path)
        self.logger.info(f"Model loaded from {self.model_path}")