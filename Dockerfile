FROM python:3.10

# Install system dependencies
COPY apt.txt /tmp/apt.txt
RUN apt-get update && \
    xargs -r -a /tmp/apt.txt apt-get install -y && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy app files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8501

# Run the app
CMD streamlit run streamlit_inference.py --server.port=8501 --server.address=0.0.0.0
