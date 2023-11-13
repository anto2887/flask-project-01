# Using Python 3.9 slim image as the base
FROM python:3.9-slim
RUN ln -snf /usr/share/zoneinfo/America/Chicago /etc/localtime && echo America/Chicago > /etc/timezone

# Setting the working directory to /flaskr
WORKDIR /flaskr


COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy only the necessary files and directories
# If you have more directories like templates or static, add them here
COPY . .
COPY wait-for-it.sh /usr/local/bin/wait-for-it.sh
COPY entrypoint.sh /flaskr/entrypoint.sh

# Provide the necessary permissions
RUN chmod +x /usr/local/bin/wait-for-it.sh /flaskr/entrypoint.sh

# Exposing port 5000 for the Flask app to listen on
EXPOSE 5000

# Setting Flask environment variables
ENV FLASK_APP=app
ENV PYTHONPATH /app
ENV CREATE_TABLES_ON_STARTUP=True
