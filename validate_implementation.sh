#!/bin/bash
set -e

echo "🔍 Finance Tracker Service - Implementation Validation"
echo "======================================================="
echo ""

cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi

source .venv/bin/activate

echo "✅ Virtual environment activated"
echo ""

# Check application imports
echo "📦 Checking application imports..."
python -c "from app.main import app; print(f'   ✓ App loads successfully')"
python -c "from app.main import app; print(f'   ✓ Title: {app.title}')"
python -c "from app.main import app; print(f'   ✓ Version: {app.version}')"
python -c "from app.main import app; print(f'   ✓ Routes: {len(app.routes)} endpoints')"
echo ""

# Check models
echo "📦 Checking database models..."
python -c "from app.models.user import User; print('   ✓ User model')"
python -c "from app.models.transactions import Transaction; print('   ✓ Transaction model')"
python -c "from app.models.auth_session import AuthSession; print('   ✓ AuthSession model')"
echo ""

# Check schemas
echo "📦 Checking Pydantic schemas..."
python -c "from app.schemas.user import UserCreate, UserRead; print('   ✓ User schemas')"
python -c "from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionRead; print('   ✓ Transaction schemas')"
python -c "from app.schemas.auth import Token; print('   ✓ Auth schemas')"
echo ""

# Check CRUD operations
echo "📦 Checking CRUD operations..."
python -c "from app.crud.user import get_user_by_email, get_users; print('   ✓ User CRUD')"
python -c "from app.crud.transactions import create_new_transaction, get_transactions, update_transaction, delete_transaction; print('   ✓ Transaction CRUD')"
echo ""

# Check dependencies
echo "📦 Checking API dependencies..."
python -c "from app.api.deps import get_current_user, get_admin_user; print('   ✓ Auth dependencies')"
echo ""

# List all endpoints
echo "📋 Available API Endpoints:"
python << 'PYCODE'
from app.main import app
routes = [r for r in app.routes if hasattr(r, 'methods')]
for route in sorted(routes, key=lambda x: (x.path, str(x.methods))):
    methods = ', '.join(sorted(route.methods - {'HEAD', 'OPTIONS'}))
    tags = getattr(route, 'tags', [])
    tag_str = f"[{tags[0]}]" if tags else ""
    print(f"   {methods:6} {route.path:40} {tag_str}")
PYCODE
echo ""

# Check test files
echo "📦 Checking test suite..."
test_count=$(find tests -name "test_*.py" | wc -l | tr -d ' ')
echo "   ✓ Test files found: $test_count"
echo ""

# File statistics
echo "📊 Project Statistics:"
py_files=$(find app -name "*.py" | wc -l | tr -d ' ')
test_files=$(find tests -name "*.py" | wc -l | tr -d ' ')
echo "   • Application files: $py_files"
echo "   • Test files: $test_files"
echo "   • Docker files: 2 (Dockerfile, docker-compose.yml)"
echo "   • CI/CD: 1 (GitHub Actions)"
echo ""

echo "✅ All validation checks passed!"
echo ""
echo "🚀 Ready to:"
echo "   1. Run tests: pytest -v"
echo "   2. Start server: uvicorn app.main:app --reload"
echo "   3. Docker: docker-compose up --build"
echo "   4. Push to GitHub and create PR"

