from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from sqlalchemy.exc import IntegrityError

from src.models.models import Category
from src.transaction_categorization.categorize import EnhancedTransactionCategorizationService
from src.transaction_categorization.model_trainer import train_model
from src.utils.config_utils import config
from src.utils.logging_utils import setup_logger
from src.database.db_utils import CategoryService, TransactionService, get_transaction_service, get_category_service
from src.utils.utils import RedisQueue

logger = setup_logger(__name__)

def process_transaction(
    transaction: dict,
    redis_client: RedisQueue,
    categorization_service: EnhancedTransactionCategorizationService,
    transactionDBService: TransactionService = get_transaction_service(),
    categoryDBService: CategoryService = get_category_service(),
    
) -> None:
    try:
        # Use Redis to check if this transaction has been processed recently
        transaction_key = f"processed_transaction:{transaction['id']}"
        if redis_client.get(transaction_key):
            logger.info(f"Transaction {transaction['id']} was recently processed. Skipping.")
            return

        # Set a flag in Redis to indicate this transaction is being processed
        redis_client.setex(transaction_key, 300, "1")  # Expires in 5 minutes

        # Check if the transaction has already been categorized
        existing_transaction = transactionDBService.get_transaction(transaction['id'])
        if existing_transaction and existing_transaction.category_id:
            logger.info(f"Transaction {transaction['id']} already categorized. Skipping.")
            return

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
        
        categ: Category = categoryDBService.get_category_by_name(category)

        if not categ:
            logger.error(f"Category not found: {category}")
            return

        try:
            update_result = transactionDBService.update_transaction(
                transaction['id'], 
                {"category_id": categ.id}
            )
            
            if update_result:
                logger.info(f"Database update successful for transaction {transaction['id']}")
            else:
                logger.warning(f"Database update failed for transaction {transaction['id']}")
        except IntegrityError:
            logger.warning(f"IntegrityError: Transaction {transaction['id']} may already be updated.")
    
    except Exception as e:
        logger.error(f"Error processing transaction: {str(e)}")
        logger.error(f"Problematic transaction: {transaction}")
    finally:
        # Remove the processing flag from Redis
        redis_client.delete(transaction_key)

def worker(
    queue: RedisQueue,
    categorization_service: EnhancedTransactionCategorizationService,
    batch_size: int
) -> None:
    while True:
        try:
            transaction_generator = queue.dequeue_batch(batch_size, timeout=0.1)
            transactions_processed = 0
            
            for transaction in transaction_generator:
                transactions_processed += 1
                try:
                    logger.info(f"Thread {threading.current_thread().name} processing transaction: {transaction.get('id', 'Unknown ID')}")
                    process_transaction(transaction, categorization_service)
                    logger.info(f"Thread {threading.current_thread().name} successfully processed transaction: {transaction.get('id', 'Unknown ID')}")
                except Exception as e:
                    logger.error(f"Error processing transaction: {str(e)}")
                    logger.error(f"Problematic transaction: {transaction}")
            
            if transactions_processed > 0:
                logger.info(f"Thread {threading.current_thread().name} processed {transactions_processed} transactions")
            else:
                logger.debug(f"Thread {threading.current_thread().name} found no transactions to process")
                
        except StopIteration:
            # This exception shouldn't be raised if dequeue_batch is implemented correctly,
            # but we'll handle it just in case
            logger.debug(f"Thread {threading.current_thread().name} completed batch processing")
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
            executor.submit(process_batch, queue, categorization_service, batch_size)
            for _ in range(num_workers)
        ]
        
        for future in futures:
            try:
                future.result()
            except Exception as e:
                logger.error(f"Worker thread failed: {str(e)}")

def process_batch(
    queue: RedisQueue,
    categorization_service: EnhancedTransactionCategorizationService,
    batch_size: int
) -> None:
    transaction_generator = queue.dequeue_batch(batch_size, timeout=0.1)
    transactions_processed = 0
    
    for transaction in transaction_generator:
        transactions_processed += 1
        try:
            logger.info(f"Thread {threading.current_thread().name} processing transaction: {transaction.get('id', 'Unknown ID')}")
            process_transaction(transaction,queue, categorization_service)
            logger.info(f"Thread {threading.current_thread().name} successfully processed transaction: {transaction.get('id', 'Unknown ID')}")
        except Exception as e:
            logger.error(f"Error processing transaction: {str(e)}")
            logger.error(f"Problematic transaction: {transaction}")
    
    if transactions_processed > 0:
        logger.info(f"Thread {threading.current_thread().name} processed {transactions_processed} transactions")
    else:
        logger.debug(f"Thread {threading.current_thread().name} found no transactions to process")

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
        
        while True:
            run_processing(queue, categorization_service, config["performance"]["max_concurrent_workers"], config["performance"]["batch_size"])
            
            # Add a small delay to prevent excessive CPU usage when the queue is empty
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error in main function: {str(e)}")

if __name__ == "__main__":
    main()