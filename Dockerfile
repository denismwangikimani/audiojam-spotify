# Use Alpine as it's a smaller base image
FROM python:3.10-alpine

# Install build dependencies for compiling packages
RUN apk add --no-cache gcc g++ musl-dev libc-dev

# Set work directory
WORKDIR /app

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies and clean up in one layer
RUN pip install --no-cache-dir -r requirements.txt && \
    find /usr/local -depth \
    \( \
    \( -type d -a -name test -o -name tests \) \
    -o \
    \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
    \) -exec rm -rf '{}' +

# Copy the rest of the application
COPY . .

# Set the command to run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
