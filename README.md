# Flaskr Web Application

Flaskr is a web application designed to automate a score prediction game for the English Premier League. The application scrapes weekly match scores from FBref.com and uses a scheduler function to evaluate and determine the best performer at the end of each match week.

## Features

- **User Registration and Authentication**: Users can register, log in, and log out.
- **Blog Management**: Authenticated users can create, read, update, and delete blog posts.
- **Database Initialization**: On application startup, it automatically checks the database connection and creates necessary tables if they don't exist.
- **Scraper Function**: Scrapes weekly English Premiership scores from FBref.com.
- **Scheduler Function**: Runs at the end of match weeks to determine the best performer.
- **Docker Deployment**: The application is containerized using Docker.
- **AWS ECS Deployment**: Infrastructure is managed and deployed using Terraform on AWS ECS.

## Setup & Installation

### Prerequisites

- Docker
- AWS CLI configured
- Terraform installed

### Steps

1. **Install Docker**:

    Follow the instructions for your operating system from the [official Docker documentation](https://docs.docker.com/get-docker/).

2. **Clone the Repository**:

    ```bash
    git clone https://gitlab.com/anto2887/vpc-deployement.git
    cd flaskr
    ```

3. **Build the Docker Image**:

    ```bash
    docker build -t flaskr-app .
    ```

4. **Push the Docker Image to Amazon ECR**:

    - **Create a repository in Amazon ECR** (if not already created):

        ```bash
        aws ecr create-repository --repository-name flaskr-app
        ```

    - **Authenticate Docker to your Amazon ECR registry**:

        ```bash
        aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com
        ```

    - **Tag your Docker image**:

        ```bash
        docker tag flaskr-app:latest <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/flaskr-app:latest
        ```

    - **Push the Docker image to ECR**:

        ```bash
        docker push <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/flaskr-app:latest
        ```

5. **Initialize Terraform**:

    ```bash
    terraform init
    ```

6. **Plan the Terraform Deployment**:

    ```bash
    terraform plan
    ```

7. **Apply the Terraform Configuration**:

    ```bash
    terraform apply
    ```

   This command will create the necessary AWS resources and deploy the application to ECS.

8. **Access the Application**:

    After the deployment is complete, you can access the application using the DNS name of the AWS ALB created by Terraform.

## Debugging

If you face issues related to database tables not being created:

1. Ensure that the `CREATE_TABLES_ON_STARTUP` environment variable is set to `True` in your ECS task definition.
2. Check the application logs in CloudWatch for relevant error messages.

## Contributing

Feel free to fork this repository, make changes, and submit pull requests. If you find any bugs or have feature requests, please open an issue in the repository.

---