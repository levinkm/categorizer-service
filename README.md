# Transaction Categorizer

## Overview

This project implements a transaction categorizer that reads transactions from a Redis queue, categorizes them using machine learning and rule-based approaches, and updates the results in a database. It's designed to process financial transactions efficiently and accurately.

## Project Structure

```
.
├── app.py
├── compose.yaml
├── config.yaml
├── Dockerfile
├── logs
│   └── app.log
├── model_files
│   ├── training_data.joblib
│   └── transaction_categorization_model.joblib
├── requirements.txt
├── scheduler.py
└── src
    ├── database
    │   ├── db_connector.py
    │   └── db_utils.py
    ├── models
    │   └── models.py
    ├── transaction_categorization
    │   ├── categorization_rules.py
    │   ├── categorize.py
    │   ├── data_loader.py
    │   └── model_trainer.py
    └── utils
        ├── category_files
        │   ├── keyword_categories.yaml
        │   └── merchant_categories.yaml
        ├── config_utils.py
        ├── logging_utils.py
        └── utils.py
```

## Key Components

1. **Redis Queue**: Transactions are read from a Redis queue for processing.
2. **Categorization Engine**: Utilizes both machine learning (ML) and rule-based approaches for accurate categorization.
3. **Database Connector**: Manages connections and updates to the database.
4. **Scheduler**: Manages the timing and flow of ml model updation.

## Setup and Installation

1. Clone the repository:
   ```
   git clone [repository-url]
   cd transaction-categorizer
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up Redis:
   - Ensure Redis is installed and running on your system.
   - Update the Redis connection details in `config.yaml`.

4. Configure the database:
   - Update database connection details in `config.yaml`.


## Running the Application

1. Start the main application:
   ```
   python -m app
   ```

2. (Optional) Run the scheduler separately:
   ```
   python scheduler.py
   ```

## Configuration

Adjust settings in `config.yaml`:
- Redis connection details
- Database connection details
- Model file paths
- Logging configurations

## Docker Support

To run the application using Docker:

1. Build the Docker image:
   ```
   docker build -t transaction-categorizer .
   ```

2. Run the container:
   ```
   docker-compose up -d
   ```

Refer to `README.Docker.md` for more detailed Docker instructions.

<!-- ## Testing

Run tests using:
```
python test.py
``` -->

## Logging

Logs are stored in `logs/app.log`. Configure logging levels in `config.yaml`.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<!-- ## License

[Specify your license here] -->

## Contact

FedhaTrac - fedhatrac@gmail.com

Project Link: [https://github.com/Fedharac/fedhatrac-categorizer-service](https://github.com/levin-mutai/fedhatrac-categorizer-service)