# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
#COPY .env .env


# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80
EXPOSE 8501
EXPOSE 8080

# Run app.py when the container launches
ENTRYPOINT ["streamlit","run","streamlit/SightSea_AI_Demo.py","--server.port=8080","--server.address=0.0.0.0"]