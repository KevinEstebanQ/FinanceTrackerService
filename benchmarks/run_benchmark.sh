#!/usr/bin/env bash
# Usage: ./run_benchmark.sh <label> [users] [duration_seconds]
#
# Examples:
#   ./run_benchmark.sh baseline
#   ./run_benchmark.sh after-jwt-fix 50 90
#   ./run_benchmark.sh after-redis 100 120
#
# Results are saved to benchmarks/results/<date>_<label>/
# Run from the repo root.

set -euo pipefail

LABEL="${1:-baseline}"
USERS="${2:-50}"
DURATION="${3:-60}"

DATE=$(date +%Y-%m-%d)
OUT_DIR="benchmarks/results/${DATE}_${LABEL}"
mkdir -p "$OUT_DIR"

echo ""
echo "=== FinanceTrackerService Benchmark ==="
echo "  Label    : $LABEL"
echo "  Users    : $USERS"
echo "  Duration : ${DURATION}s"
echo "  Output   : $OUT_DIR"
echo "======================================="
echo ""

# Check services are up
check_service() {
  local url="$1" name="$2"
  if ! curl -sf "$url" > /dev/null 2>&1; then
    echo "ERROR: $name does not appear to be running at $url"
    echo "  Start with: docker compose up --build"
    exit 1
  fi
}
check_service "http://localhost:8081/health" "auth-service (port 8081)" || true
check_service "http://localhost:8080/health" "transactions-service (port 8080)"

# Run locust headlessly — both user classes, weighted 30/70 toward TransactionsUser
locust \
  -f benchmarks/locustfile.py \
  TransactionsUser \
  --headless \
  --host http://localhost:8080 \
  --users "$USERS" \
  --spawn-rate 10 \
  --run-time "${DURATION}s" \
  --csv "$OUT_DIR/transactions" \
  --html "$OUT_DIR/report.html" \
  --logfile "$OUT_DIR/locust.log" \
  2>&1 | tee "$OUT_DIR/stdout.log"

echo ""
echo "=== Auth service benchmark ==="
locust \
  -f benchmarks/locustfile.py \
  AuthServiceUser \
  --headless \
  --host http://localhost:8081 \
  --users "$USERS" \
  --spawn-rate 10 \
  --run-time "${DURATION}s" \
  --csv "$OUT_DIR/auth" \
  --logfile "$OUT_DIR/auth_locust.log" \
  2>&1 | tee -a "$OUT_DIR/stdout.log"

# Print a quick summary from the CSV stats file
echo ""
echo "=== Summary: Transactions service ==="
if [ -f "$OUT_DIR/transactions_stats.csv" ]; then
  column -t -s',' "$OUT_DIR/transactions_stats.csv"
fi

echo ""
echo "=== Summary: Auth service ==="
if [ -f "$OUT_DIR/auth_stats.csv" ]; then
  column -t -s',' "$OUT_DIR/auth_stats.csv"
fi

echo ""
echo "Full HTML report: $OUT_DIR/report.html"
echo "Done. Update benchmarks/RESULTS.md with these numbers."
