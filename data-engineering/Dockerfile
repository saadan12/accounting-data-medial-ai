# To enable ssh & remote debugging on app service change the base image to the one below
FROM mcr.microsoft.com/azure-functions/python:4-python3.8



# Install dependencies for msodbcsql18
RUN curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc
RUN curl https://packages.microsoft.com/config/debian/10/prod.list | tee /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql18

# optional: for unixODBC development headers
# RUN apt-get install -y unixodbc-dev

# Set environment variables
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

# 4. Finally, copy python code to image
COPY data-engineering /home/site/wwwroot

 

# 5. Install other packages in requirements.txt
RUN cd /home/site/wwwroot && \
    pip install -r requirements.txt
