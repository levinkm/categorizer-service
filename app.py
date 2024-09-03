from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

from src.transaction_categorization.categorize import EnhancedTransactionCategorizationService
from src.transaction_categorization.model_trainer import train_model
from src.utils.config_utils import config
from src.utils.logging_utils import setup_logger
from src.database.db_utils import CategoryService, TransactionService, get_transaction_service, get_category_service
from src.utils.utils import RedisQueue

logger = setup_logger(__name__)

def process_transaction(
    transaction: dict,
    categorization_service: EnhancedTransactionCategorizationService,
    transactionDBService: TransactionService = get_transaction_service(),
    categoryDBService: CategoryService = get_category_service()
) -> None:
    try:
        # Parse the date string to datetime object if it exists
        if 'date' in transaction:
            transaction['date'] = datetime.fromisoformat(transaction['date'])
        
        category = categorization_service.categorize_transaction(
            transaction['narration'],
            transaction['amount'],
            transaction.get('date')
        )
        
        logger.info(f"Thread {threading.current_thread().name} processed - "
              f"Transaction: {transaction['narration']}, "
              f"Amount: ${transaction['amount']:.2f}, "
              f"Date: {transaction.get('date', 'N/A')}, "
              f"Category: {category}")
        
        update_result = transactionDBService.update_transaction(
            transaction['id'], 
            {"category_id": categoryDBService.get_category_by_name(category).id}
        )
        logger.info(f"Database update result for transaction {transaction['id']}: {update_result}")
    except Exception as e:
        logger.error(f"Error processing transaction: {str(e)}")
        logger.error(f"Problematic transaction: {transaction}")
        raise  # Re-raise the exception to be caught by the worker

def worker(
    queue: RedisQueue,
    categorization_service: EnhancedTransactionCategorizationService,
    batch_size: int
) -> None:
    while True:
        try:
            batch = list(queue.dequeue_batch(batch_size, timeout=0.1))
            if batch:
                logger.info(f"Thread {threading.current_thread().name} dequeued {len(batch)} transactions")
            for transaction in batch:
                try:
                    logger.info(f"Processing transaction: {transaction['id']}")
                    process_transaction(transaction, categorization_service)
                    logger.info(f"Successfully processed transaction: {transaction['id']}")
                except Exception as e:
                    logger.error(f"Error processing transaction: {str(e)}")
                    logger.error(f"Problematic transaction: {transaction}")
        except Exception as e:
            logger.error(f"Error in worker thread {threading.current_thread().name}: {str(e)}")

def run_processing(
    queue: RedisQueue,
    categorization_service: EnhancedTransactionCategorizationService,
    num_workers: int,
    batch_size: int
) -> None:
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(worker, queue, categorization_service, batch_size)
            for _ in range(num_workers)
        ]
        
        for future in futures:
            try:
                future.result()
            except Exception as e:
                logger.error(f"Worker thread failed: {str(e)}")

def categorize_uncategorized_transactions(
    categorization_service: EnhancedTransactionCategorizationService,
    batch_size: int = 100,
    transactionDBService: TransactionService = get_transaction_service(),
    categoryDBService: CategoryService = get_category_service()
) -> None:
    while True:
        batch = transactionDBService.get_latest_transactions_with_no_category(batch_size)
        
        if not batch:
            break
        
        logger.info(f"Processing batch of {len(batch)} uncategorized transactions.")

        for transaction in batch:
            try:
                category_name = categorization_service.categorize_transaction(
                    transaction.narration,
                    transaction.amount,
                    transaction.date if transaction.date else None
                )
                logger.info(f"Uncategorized transaction: {transaction.narration} as {category_name}")
                category = (
                    categoryDBService.get_category(category_name)
                    if isinstance(category_name, int)
                    else categoryDBService.get_category_by_name(category_name)
                )

                if category:
                    transactionDBService.update_transaction(transaction.id, {"category_id": category.id})
                    logger.debug(f"Categorized transaction: {transaction.narration} as {category_name}")
                else:
                    logger.warning(f"Category not found for name: {category_name}")
            except Exception as e:
                logger.error(f"Error categorizing transaction {transaction.id}: {str(e)}")

    logger.info("Finished categorizing uncategorized transactions.")
    
def main() -> None:
    try:
        # Check database connection
        transactionDBService = get_transaction_service()
        categoryDBService = get_category_service()
        
        # Test database connection
        try:
            transactionDBService.get_latest_transactions_with_no_category(1)
            categoryDBService.get_category(2)
            logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return

        if config["features"]["train_model_on_startup"]:
            logger.info("Training model on startup...")
            train_model(config["model"]["path"], logger, transactionDBService)
        
        queue = RedisQueue(
            port=config["queue"]["port"],
            password=config["queue"]["password"],
            queue_name=config["queue"]["queue_name"],
        )
       
        categorization_service = EnhancedTransactionCategorizationService(model_path=config["model"]["path"])
        
        if config["features"]["categorize_uncategorized_on_startup"]:
            logger.info("Categorizing uncategorized transactions on startup...")
            categorize_uncategorized_transactions(categorization_service, config["performance"]["batch_size"])
        
        logger.info(f"Starting transaction processing with {config['performance']['max_concurrent_workers']} workers...")
        run_processing(queue, categorization_service, config["performance"]["max_concurrent_workers"], config["performance"]["batch_size"])
    except Exception as e:
        logger.error(f"Fatal error in main function: {str(e)}")

if __name__ == "__main__":
    main()