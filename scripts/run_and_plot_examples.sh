#!/bin/bash

SCRIPT_DIR=$(dirname "$0")

# Check if WORK_DIR is set
if [ -z "$WORK_DIR" ]; then
    echo "Error: WORK_DIR is not set. Please set it to the directory containing the scripts."
    exit 1
fi

# Run examples

uv run python $SCRIPT_DIR/run_examples.py --max_concurrent_processes 1 --num_samples 100 --seed 0

# Traverse the WareHouse directory and find .log files in nested directories
find $WORK_DIR/WareHouse -mindepth 2 -type f -name "*.log" | while read -r log_file; do
    # Define output file path based on input log file name
    output_file="${log_file%.log}_usage_info.csv"
    
    # Execute the Python script with input and output paths
    uv run python $SCRIPT_DIR/parse_usage_info.py "$log_file" "$output_file"
    uv run python $SCRIPT_DIR/plot_usage_info.py --csv_file "$output_file"
done
