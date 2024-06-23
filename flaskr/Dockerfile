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

# Copy the modified wait-for-it.sh script to the appropriate location
COPY wait-for-it.sh /usr/local/bin/wait-for-it.sh
# Provide the necessary permissions
RUN chmod +x /usr/local/bin/wait-for-it.sh

# Exposing port 80 for the Flask app to listen on
EXPOSE 80

# Setting Flask environment variables
ENV FLASK_APP=app
ENV PYTHONPATH=/flaskr
ENV CREATE_TABLES_ON_STARTUP=True

# Command to run the application, passing a notification command to wait-for-it.sh
CMD ["/usr/local/bin/wait-for-it.sh", "db:5432", "--notify=echo Connection to db successful", "--", "/flaskr/entrypoint.sh"]
