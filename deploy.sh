#!/bin/bash
# Blog project deployment script
# Usage: ./deploy.sh

set -e

echo "Deploying Blog Project..."

# Generate random passwords if not set
if [ ! -f .env ]; then
    echo "Creating .env..."
    cat > .env <<EOF
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGIN=http://localhost
DB_PASSWORD=$(openssl rand -hex 16)
EOF
    echo ".env created with random secrets."
fi

# Pull latest code
git pull origin main

# Build and start
docker compose up -d --build

# Wait for backend to be ready
echo "Waiting for backend..."
sleep 5

# Run seed data
docker compose exec -T backend python seed.py

echo ""
echo "Deployed!"
echo ""
echo "Default login: admin / admin123"
echo "Change password immediately: 右上角用户名 → 编辑资料 → 修改密码"
