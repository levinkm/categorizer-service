import time
import yaml
from typing import Dict, Generator, List
import os
import json
import redis

from src.utils.logging_utils import setup_logger

logger = setup_logger(__name__)

class CategoryLoader:

    def __init__(self, category_folder: str):
        self.category_folder = category_folder

    def _read_yaml_file(self, file_name: str) -> dict:
        file_path = os.path.join(current_directory, category_folder, file_name)
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)

    def _load_keyword_categories(self) -> Dict[str, List[str]]:
        return self._read_yaml_file('keyword_categories.yaml')

    def _load_merchant_categories(self) -> Dict[str, str]:
        return self._read_yaml_file('merchant_categories.yaml')

# Usage example:
category_folder = 'category_files'
current_directory = os.path.dirname(os.path.abspath(__file__))

loader = CategoryLoader(category_folder)


class RedisQueue:
    def __init__(self, host='localhost', port=6379, db=0, password=None, queue_name='default_queue'):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )
        self.queue_name = queue_name

    def enqueue(self, item):
        """Add an item to the queue."""
        serialized_item = json.dumps(item)
        self.redis_client.rpush(self.queue_name, serialized_item)

    def dequeue_batch(self, batch_size: int = 10, timeout: int = 5) -> Generator[dict, None, None]:
        """
        Remove and return items from the queue in batches.
        If the queue is empty, it will wait for 'timeout' seconds before checking again.
        """
        while True:
            pipe = self.redis_client.pipeline()
            pipe.lrange(self.queue_name, 0, batch_size - 1)
            pipe.ltrim(self.queue_name, batch_size, -1)
            results, _ = pipe.execute()

            if not results:
                # Wait for a short time before checking again
                time.sleep(timeout)
                continue

            logger.info(f"Found and dequeued {len(results)} item(s) from the queue.")
            for item in results:
                try:
                    yield json.loads(item)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error for item: {item[:100]}... Error: {str(e)}")
                    self.redis_client.rpush("error_queue", item)

    def is_empty(self):
        """Check if the queue is empty."""
        return self.size() == 0

    def size(self):
        """Return the current size of the queue."""
        return self.redis_client.llen(self.queue_name)

    def clear(self):
        """Remove all items from the queue."""
        self.redis_client.delete(self.queue_name)