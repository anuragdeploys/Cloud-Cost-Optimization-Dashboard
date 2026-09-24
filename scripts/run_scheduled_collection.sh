#!/bin/bash

set -e

PROJECT_DIR="/root/cloud-cost-optimization-dashboard"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/scheduled_collection.log"

mkdir -p "$LOG_DIR"

cd "$PROJECT_DIR"

source "$PROJECT_DIR/venv312/bin/activate"

echo "----------------------------------------" >> "$LOG_FILE"
echo "Scheduled collection started: $(date)" >> "$LOG_FILE"

if python -c "
from app.config import is_aws_collection_enabled
raise SystemExit(
    0 if is_aws_collection_enabled() else 1
)
"; then

    if python -c "
from app.scheduler import run_scheduled_collection

result = run_scheduled_collection()

print('Scheduled AWS collection completed.')
print(f'Records received: {result[\"records_received\"]}')
print(f'Records inserted: {result[\"records_inserted\"]}')
print(f'Duplicates ignored: {result[\"duplicates_ignored\"]}')
print(f'Total cost: {result[\"total\"]:.2f} {result[\"currency\"]}')
" >> "$LOG_FILE" 2>&1; then

        echo "Scheduled AWS collection succeeded." >> "$LOG_FILE"

    else

        collection_status=$?

        echo "Scheduled AWS collection FAILED." >> "$LOG_FILE"
        echo "Exit code: $collection_status" >> "$LOG_FILE"
        echo "Scheduled collection finished: $(date)" >> "$LOG_FILE"

        exit "$collection_status"

    fi

else

    python -c "
from app.scheduler import calculate_daily_collection_period

start_date, end_date = calculate_daily_collection_period()

print(
    f'DRY RUN: would collect '
    f'{start_date} to {end_date}'
)
" >> "$LOG_FILE"

    echo "AWS collection disabled." >> "$LOG_FILE"

fi

echo "Scheduled collection finished: $(date)" >> "$LOG_FILE"
