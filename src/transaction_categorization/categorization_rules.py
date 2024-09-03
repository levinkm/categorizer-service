from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from sklearn.pipeline import Pipeline

from src.database.db_utils import get_category_service

def match_by_keyword(narration: str, keyword_categories: Dict[str, List[str]]) -> Optional[str]:
    """Match transaction by keywords in the narration."""
    narration_lower = narration.lower()
    for category, keywords in keyword_categories.items():
        if any(keyword in narration_lower for keyword in keywords):
            return category
    return None

def match_by_merchant(narration: str, merchant_categories: Dict[str, str]) -> Optional[str]:
    """Match transaction by merchant name in the narration."""
    for merchant, category in merchant_categories.items():
        if merchant in narration.upper():
            return category
    return None

def categorize_by_ml(narration: str, amount: float, model: Pipeline) -> str:
    """Categorize transaction using the machine learning model."""
    features = pd.DataFrame({'narration': [narration], 'amount': [amount]})
    prediction = model.predict(features)
    category_id = int(prediction[0])  
    return get_category_service().get_category(category_id).name

def categorize_by_amount(narration: str, amount: float, date: Optional[datetime]) -> Optional[str]:
    """Categorize transaction based on the amount."""
    if amount > 5000:
        return 'large_expenses'
    elif amount < 10:
        return 'small_expenses'
    return None

def categorize_by_date(date: datetime) -> Optional[str]:
    """Categorize transaction based on the date."""
    if date.month == 12 or date.month == 1:
        return 'holiday_expenses'
    elif date.weekday() >= 5:  # Saturday or Sunday
        return 'weekend_expenses'
    return None