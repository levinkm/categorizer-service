import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from src.database.db_utils import TransactionService
from src.transaction_categorization.text_utils import text_processor
from src.transaction_categorization.data_loader import load_training_data

def load_or_train_model(model_path: str, logger: logging.Logger, transactionDB: TransactionService) -> Pipeline:
    """Load the existing model or train a new one if not found."""
    try:
        model = joblib.load(model_path)
        logger.info(f"Model loaded from {model_path}")
        return model
    except FileNotFoundError:
        logger.info("Model not found. Training a new one...")
        return train_model(model_path, logger, transactionDB)
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise

def train_model(model_path: str, logger: logging.Logger, transactionDB: TransactionService) -> Pipeline:
    """Train a new machine learning model for transaction categorization."""
    try:
        data = load_training_data(transactionDB)

        # Ensure correct separation of features
        X = data[['narration', 'amount']]  # Keep it as a DataFrame
        y = data['category_id']  # Assuming 'category_id' is the target variable

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        logger.info(f"X_train shape: {X_train.shape}")
        logger.info(f"y_train shape: {y_train.shape}")

        # Define the preprocessing for different feature types
        preprocessor = ColumnTransformer(
            transformers=[
                ('text', TfidfVectorizer(analyzer=text_processor, max_features=1000), 'narration'),
                ('num', StandardScaler(), ['amount'])  # Keep 'amount' as a list to ensure it's a DataFrame
            ],
            remainder='passthrough'
        )

        # Create the full pipeline
        model = Pipeline([
            ('preprocessor', preprocessor),
            ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
        ])

        # Train the model
        model.fit(X_train, y_train)

        # Evaluate the model
        evaluate_model(model, X_test, y_test, logger)

        # Save the model
        joblib.dump(model, model_path)
        logger.info(f"Model saved to {model_path}")
        return model

    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        raise
def evaluate_model(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series, logger: logging.Logger) -> None:
    """Evaluate the trained model and log the results."""
    try:
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"Model accuracy: {accuracy:.2f}")
        logger.info("\nClassification Report:\n" + classification_report(y_test, y_pred))
    except Exception as e:
        logger.error(f"Error evaluating model: {str(e)}")
        raise

def update_model(model: Pipeline, new_data: pd.DataFrame, model_path: str, logger: logging.Logger) -> Pipeline:
    """Update the model with new training data."""
    try:
        logger.info(f"Updating model with new data: {len(new_data)} records")
    
        existing_data = joblib.load('training_data.joblib')
        updated_data = pd.concat([existing_data, new_data], ignore_index=True)
    
        X = updated_data[['narration', 'amount']]
        y = updated_data['category_id']  # Assuming 'category_id' is the target variable
        model.fit(X, y)
    
        joblib.dump(model, model_path)
        joblib.dump(updated_data, 'training_data.joblib')
        logger.info("Model updated and saved")
        return model
    except Exception as e:
        logger.error(f"Error updating model: {str(e)}")
        raise