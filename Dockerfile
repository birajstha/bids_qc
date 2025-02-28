# Use a base image that includes git and bash
FROM python:3.11-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --upgrade pip
RUN pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Create the necessary directories
RUN mkdir -p /cpac_output_dir /qc_dir /config

# Set the entrypoint to run the application
ENTRYPOINT ["python3", "/app/run.py"]
CMD ["--n_procs"]