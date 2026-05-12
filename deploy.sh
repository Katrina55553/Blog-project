#!/bin/bash
# Blog project deployment script
# Usage: ./deploy.sh [domain]

set -e

DOMAIN=${1:-localhost}
echo "Deploying for domain: $DOMAIN"

# Pull latest code
git pull origin main

# Set CORS origin
export CORS_ORIGIN="https://$DOMAIN"

# Build and start
docker compose up -d --build

# Wait for backend to start
sleep 3

# Run seed data
docker compose exec -T backend python seed.py

echo ""
echo "Deployed! Visit https://$DOMAIN"
echo ""
echo "Default login: admin / admin123"
echo "Change password immediately!"
