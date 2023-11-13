
# Flaskr Web Application

Flaskr is a simple web application built on the Flask framework. It showcases basic CRUD operations, user authentication, and blog post management. The application uses a PostgreSQL database backend to persist data, and integrates with Flask-SQLAlchemy for ORM capabilities.

## Features

- **User Registration and Authentication**: Users can register, log in, and log out. 
- **Blog Management**: Authenticated users can create, read, update, and delete blog posts.
- **Database Initialization**: On application startup, it automatically checks the database connection and creates necessary tables if they don't exist.
- **Cron Jobs**: Automated tasks using the Advanced Python Scheduler (APScheduler) module.
- **Docker Deployment**: The application is containerized using Docker and orchestrated with Docker Compose, allowing for easy deployment.

## Setup & Installation

### Prerequisites

- Docker
- Docker Compose

### Steps

1. **Clone the Repository**:

    ```bash
    git clone https://gitlab.com/anto2887/vpc-deployement.git
    cd flaskr
    ```

2. **Environment Variables**:
   
   Ensure that the environment variables are set up correctly in the Docker Compose file. Especially ensure that `SQLALCHEMY_DATABASE_URI` and `CREATE_TABLES_ON_STARTUP` are set according to your needs.

3. **Build & Start the Docker Compose Services**:

    ```bash
    docker-compose up --build
    ```

   This command will build the Docker images as per the provided Dockerfile and Docker Compose configuration, and start the necessary services.

4. **Access the Application**:

    After the services are up and running, you can access the application by visiting `http://localhost:5000` in your browser.

## Debugging

If you face issues related to database tables not being created:

1. Ensure that the `CREATE_TABLES_ON_STARTUP` environment variable is set to `True` in your Docker Compose file.
2. Check the application logs for relevant error messages.

## Contributing

Feel free to fork this repository, make changes, and submit pull requests. If you find any bugs or have feature requests, please open an issue in the repository.

