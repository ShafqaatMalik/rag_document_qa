#!/bin/bash

# AWS EC2 Setup Script for RAG Document Q&A
# Run this on a fresh Ubuntu 22.04 EC2 instance

set -e

echo "=== Starting EC2 Setup for RAG Document Q&A ==="

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "Installing Docker..."
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
echo "Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
echo "Installing Git..."
sudo apt-get install -y git

# Clone repository (update with your repo)
echo "Cloning repository..."
cd /home/ubuntu
# git clone https://github.com/yourusername/rag-document-qa.git
# cd rag-document-qa

# Create .env file
echo "Creating .env file..."
cat > .env << EOF
GEMINI_API_KEY=your_api_key_here
DEBUG=False
LOG_LEVEL=INFO
CHROMA_PERSIST_DIRECTORY=/app/chroma_data
EOF

echo "Please edit .env file with your actual API key:"
echo "nano .env"

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/rag-qa.service > /dev/null <<EOF
[Unit]
Description=RAG Document Q&A Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/rag-document-qa
ExecStart=/usr/local/bin/docker-compose -f deployment/docker/docker-compose.yml up -d
ExecStop=/usr/local/bin/docker-compose -f deployment/docker/docker-compose.yml down
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

# Install Nginx (optional reverse proxy)
echo "Installing Nginx..."
sudo apt-get install -y nginx

# Configure Nginx
sudo tee /etc/nginx/sites-available/rag-qa > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/rag-qa /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Install Certbot for SSL (optional)
echo "Installing Certbot for SSL..."
sudo apt-get install -y certbot python3-certbot-nginx

echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env file: nano .env"
echo "2. Build and start: docker-compose -f deployment/docker/docker-compose.yml up -d"
echo "3. Enable service: sudo systemctl enable rag-qa"
echo "4. Start service: sudo systemctl start rag-qa"
echo "5. Check status: sudo systemctl status rag-qa"
echo "6. View logs: docker-compose -f deployment/docker/docker-compose.yml logs -f"
echo ""
echo "For SSL: sudo certbot --nginx -d yourdomain.com"
