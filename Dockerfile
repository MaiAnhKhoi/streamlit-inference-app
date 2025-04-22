FROM python:3.10

# Install system dependencies
COPY apt.txt /tmp/apt.txt
RUN apt-get update && \
    xargs -r -a /tmp/apt.txt apt-get install -y && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app files
COPY . .

# Expose port for Streamlit
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "streamlit_inference.py", "--server.port=8501", "--server.address=0.0.0.0"]
