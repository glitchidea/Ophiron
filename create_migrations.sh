#!/bin/bash

# Create Migrations Script
# This script creates and applies new migration files

set -e  # Stop script on error

# For colored output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Django Migration Create Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Check and activate virtual environment
echo -e "${BLUE}[1/3] Checking virtual environment...${NC}"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Local venv activated${NC}"
elif [ -d "/home/jonh/Desktop/ophiron/venv" ]; then
    source /home/jonh/Desktop/ophiron/venv/bin/activate
    echo -e "${GREEN}✓ Ophiron venv activated${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment not found, using system Python${NC}"
fi

echo ""
echo -e "${BLUE}[2/3] Creating new migration files...${NC}"
# Create new migration files
python manage.py makemigrations
echo -e "${GREEN}✓ Migration files created${NC}"

echo ""
echo -e "${BLUE}[3/3] Applying migrations...${NC}"
# Apply migrations
python manage.py migrate
echo -e "${GREEN}✓ Migrations applied${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ Operation completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "  1. Create superuser: python manage.py createsuperuser"
echo "  2. Start server: python manage.py runserver"
echo ""

