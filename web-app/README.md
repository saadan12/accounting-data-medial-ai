# Django Chatbot Project
## Overview
This Django project integrates a chatbot Proof of Concept (POC) using Azure AI Search, Azure OpenAI, and Azure SQL Database. The chatbot is designed to answer user questions based on predefined knowledge stored in an Azure SQL Database and utilizes the capabilities of Azure AI Search and Azure OpenAI for natural language processing.

## Prerequisites
Before running the Django project, ensure you have the following installed:

1. Python (version 3.6 or higher)
2. Django (version 3.0 or higher)
3. Azure SDK for Python
4. Azure SQL Database
5. Azure AI Search
6. Azure OpenAI API key

## Installation
Clone this repository to your local machine:
bash

Copy code
```
git clone https://github.com/triplek-tech/sql-chatbot-poc.git
```
Create Virtual Environment
bash
```
python -m venv env
```
Activate the virtual env
```
source env/bin/activate
```
Install the required Python packages using pip:
bash
Copy code
```
cd django-app/
```
```
pip install -r requirements.txt
```
Set up your Azure resources including Azure SQL Database, Azure AI Search, and obtain the Azure OpenAI API key.
Configure your Django project settings to include the Azure SQL Database and Azure OpenAI API key.
Migrate the database:
bash
Copy code
```
python manage.py migrate
```
## Usage
### Run the Django development server:
bash
Copy code
```
python manage.py runserver
```
Access the application in your web browser at http://localhost:8000.
Interact with the chatbot by asking questions and observing the responses.
## Integration with Azure AI Search
Azure AI Search is integrated into the Django project to provide fast and relevant search results based on user queries. The chatbot leverages Azure AI Search to retrieve relevant information from the Azure SQL Database based on user input.

## Integration with Azure OpenAI
Azure OpenAI is integrated into the Django project to enhance the natural language understanding capabilities of the chatbot. By leveraging Azure OpenAI, the chatbot is able to understand and respond to user queries in a more human-like manner.
