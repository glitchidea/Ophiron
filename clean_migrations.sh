#!/bin/bash

# Clean Migrations Script
# This script cleans migration files and database only

set -e  # Stop script on error

# For colored output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Django Migration Clean Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${YELLOW}⚠️  WARNING: This operation will:${NC}"
echo "  1. Delete all migration files (except __init__.py)"
echo "  2. Delete SQLite database"
echo "  3. Clean Python cache files"
echo ""
echo -e "${RED}⚠️  ALL YOUR DATA WILL BE DELETED!${NC}"
echo ""

# Request confirmation
read -p "Do you want to continue? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${RED}Operation cancelled.${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}[1/3] Deleting migration files...${NC}"
# Delete all migration files (except __init__.py, excluding venv)
MIGRATION_COUNT=$(find . -path "*/migrations/*.py" -not -path "./venv/*" -not -name "__init__.py" -type f | wc -l)
find . -path "*/migrations/*.py" -not -path "./venv/*" -not -name "__init__.py" -type f -delete
echo -e "${GREEN}✓ ${MIGRATION_COUNT} migration files deleted${NC}"

echo ""
echo -e "${BLUE}[2/3] Deleting database...${NC}"
# Delete SQLite database
if [ -f "db.sqlite3" ]; then
    rm -f db.sqlite3
    echo -e "${GREEN}✓ Database deleted (db.sqlite3)${NC}"
else
    echo -e "${YELLOW}⚠ Database not found, skipping${NC}"
fi

echo ""
echo -e "${BLUE}[3/3] Cleaning cache files...${NC}"
# Clean Python cache files
PYCACHE_COUNT=$(find . -type d -name "__pycache__" -not -path "./venv/*" 2>/dev/null | wc -l)
find . -type d -name "__pycache__" -not -path "./venv/*" -exec rm -rf {} + 2>/dev/null || true
PYC_COUNT=$(find . -name "*.pyc" -not -path "./venv/*" 2>/dev/null | wc -l)
find . -name "*.pyc" -not -path "./venv/*" -delete 2>/dev/null || true
echo -e "${GREEN}✓ ${PYCACHE_COUNT} __pycache__ folders and ${PYC_COUNT} .pyc files cleaned${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ Cleanup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "  1. Create new migrations: python manage.py makemigrations"
echo "  2. Apply migrations: python manage.py migrate"
echo "  3. Create superuser: python manage.py createsuperuser"
echo ""

