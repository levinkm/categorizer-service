
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from src.transaction_categorization.categorize import EnhancedTransactionCategorizationService
from src.transaction_categorization.data_loader import load_training_data,load_update_data
from src.utils.config_utils import config
from src.utils.logging_utils import setup_logger
from src.database.db_utils import get_transaction_service

logger = setup_logger(__name__)



def daily_training(config):
    print(f"Starting daily training at {datetime.now()}")
    
    # Initialize the service
    service = EnhancedTransactionCategorizationService(model_path=config['model']['path'])
    
    # Load new data
    new_data = load_training_data(get_transaction_service())
    
    # Update the model with new data
    service.update_model(new_data)
    
    print(f"Daily training completed at {datetime.now()}")

def main():

    # Check if model exists, if not, train it
    
    service = EnhancedTransactionCategorizationService(model_path=config['model']['path'])

    # Load initial training data and train the model
    initial_data = load_update_data(get_transaction_service())
    service.update_model(initial_data)
    logger.info("Initial model training completed.")

    scheduler = BackgroundScheduler()
    
    # Schedule the job to run at the specified time every day
    start_time = datetime.strptime(config['scheduler']['start_time'], "%H:%M").time()
    scheduler.add_job(daily_training, 'interval', 
                      hours=config['scheduler']['update_interval_hours'], 
                      start_date=datetime.combine(datetime.now().date(), start_time),
                      args=[config])
    
    scheduler.start()

    logger.info(f"Scheduler started. Daily training will occur at {start_time}")

    try:
        # Keep the script running
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        
        scheduler.shutdown()
        print("Scheduler shut down.")

if __name__ == "__main__":
    main()