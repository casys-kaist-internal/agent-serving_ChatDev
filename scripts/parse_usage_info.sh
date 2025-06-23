#!/bin/bash

# Traverse the WareHouse directory and find .log files in nested directories
find WareHouse -mindepth 2 -type f -name "*.log" | while read -r log_file; do
    # Define output file path based on input log file name
    output_file="${log_file%.log}_usage_info.csv"
    
    # Execute the Python script with input and output paths
    python3 parse_usage_info.py "$log_file" "$output_file"
done
