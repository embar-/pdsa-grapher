FROM python:3.12-alpine

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py ./main.py
COPY assets ./assets
COPY grapher_lib ./grapher_lib
COPY locale ./locale
COPY locale_utils ./locale_utils

# Expose the port the app runs on
EXPOSE 80

# Command to run the application
CMD gunicorn -b 0.0.0.0:80 main:server