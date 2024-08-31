# Medial-AI

Medial-AI is a platform designed to retrieve user data from the Xero website for their organization. Users can ask the chatbot questions related to their data.

## Overview

The project consists of two main components:

1. **Django Web Application:**
   - Frontend and backend functionalities are implemented using Django.
   - SQL is used as the database to store and manage data.
   - We use Stripe for Payment
   - We used the GPT-4o model from OpenAI for question answering.

2. **Azure Serverless function:**
   - Azure Serverless function are utilized to fetch data from the Xero..
   - The retrieved data from the Xero of Accounting API is stored in the following tables.:
     - Accounts
     - Attachment
     - Bank Transaction
     - Budget
     - Contacts
     - Credit Notes
     - Employee
     - Expense Claims
     - Invoices
     - Item
     - Journals
     - Payment
     - Ourchase Order
     - Quotes
     - Receipts
     - Reports
       - Aged Paybale by Contacts
       - Aged Receiveable by Contacts
       - Balance Sheet
       - Budget Summary
       - Profit and Loss
       - Trial Balance

## Merge `development` to `production` branch

We are using forward merging to merge the `development` branch to the `production` branch.

1. Create a pull request to merge the `development` branch to the `production` branch.

2. To merge the `development` branch to the `production` branch, run these commands in your terminal (GitHub does not support forward merging, so you have to do it manually in your terminal):

    ```bash
    git pull
    git checkout production
    git merge origin/development
    git push origin production
    ```

## Getting Started

To set up and run the project locally, follow these steps:


1. Clone the repository:

    ```bash
    git clone https://github.com/triplek-tech/medial-ai.git
    cd medial-ai/web-app
    ```

2. Make Virtual Environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install Dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run Migrations:

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5. Run Server:

    ```bash
      python manage.py runserver
    ```

6. Access the application in your web browser at `http://localhost:8000`


Azure Lamda Functions
To set up and run the aws lambda functions locally, follow these steps:

2- cd data-engineering
3- install requirements using command `pip install -r requirements.txt`
4- func start
By you can see 2 endpoints
  1-http://localhost:7071/api/accounts
  2-http://localhost:7071/api/aged_payable_by_contacts
  3-http://localhost:7071/api/aged_receiveable_by_contacts
  4-http://localhost:7071/api/get_tokens
  5-http://localhost:7071/api/reports
  6-http://localhost:7071/api/split_accounts

Environment Variables
Ensure to set the necessary environment variables for the azure serverless functions, including API keys and other configurations.

Contributing
Contributions are welcome! If you have any suggestions, improvements, or bug fixes, please feel free to open an issue or create a pull request.

