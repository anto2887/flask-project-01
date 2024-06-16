# Using Python 3.9 slim image as the base
FROM python:3.9-slim

# Set timezone
RUN ln -snf /usr/share/zoneinfo/America/Chicago /etc/localtime && echo America/Chicago > /etc/timezone

# Setting the working directory to /flaskr
WORKDIR /flaskr

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the necessary files and directories
COPY . .

# Copy the wait-for-it.sh and entrypoint.sh scripts to the appropriate locations
COPY wait-for-it.sh /usr/local/bin/wait-for-it.sh
COPY entrypoint.sh /flaskr/entrypoint.sh

# Provide the necessary permissions
RUN chmod +x /usr/local/bin/wait-for-it.sh /flaskr/entrypoint.sh

# Exposing port 5000 for the Flask app to listen on
EXPOSE 80

# Setting Flask environment variables
ENV FLASK_APP=app
ENV PYTHONPATH=/flaskr
ENV CREATE_TABLES_ON_STARTUP=True

# Command to run the application
CMD ["/usr/local/bin/wait-for-it.sh", "db:5432", "--", "/flaskr/entrypoint.sh"]
