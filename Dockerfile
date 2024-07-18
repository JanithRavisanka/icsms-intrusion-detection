# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
#EXPOSE 80

# Define environment variable
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_REGION=${AWS_REGION}
ENV GMAIL_USER=${GMAIL_USER}
ENV GMAIL_PASSWORD=${GMAIL_PASSWORD}
ENV COGNITO_POOL_ID=${COGNITO_POOL_ID}
ENV COGNITO_CLIENT_ID=${COGNITO_CLIENT_ID}
ENV DYNAMODB_TABLE_NAME=${DYNAMODB_TABLE_NAME}
ENV MONGO_URI=${MONGO_URI}
ENV SMTP_SERVER=${SMTP_SERVER}
ENV SMTP_PORT=${SMTP_PORT}


# Run app.py when the container launches
CMD ["python", "./app/app.py"]
