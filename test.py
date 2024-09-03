import redis
import json

def read_and_print_from_queue(
    queue_name: str,
    host: str = 'localhost',
    port: int = 6379,
    db: int = 0,
    password: str = 'fedhatrac',
) -> None:
    # Initialize Redis client
    redis_client = redis.Redis(
        host=host,
        port=port,
        db=db,
        password=password,
        decode_responses=True
    )
    
    while True:
        # Pop an item from the queue
        item = redis_client.lpop(queue_name)
        
        if item:
            # Convert item from JSON to dictionary (if applicable)
            try:
                item_data = json.loads(item)
            except json.JSONDecodeError:
                item_data = item  # If not JSON, print as it is
            
            print(f"Dequeued item: {item_data}")
        else:
            print("Queue is empty. Waiting for new items...")
            break  # Exit the loop when the queue is empty

# Usage example
read_and_print_from_queue('uncategorized_transactions')
