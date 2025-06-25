import subprocess
import os
import csv
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from argparse import ArgumentParser

WORK_DIR = os.getenv('WORK_DIR')
assert WORK_DIR is not None, "WORK_DIR environment variable not set"
assert 'ChatDev' in WORK_DIR, f"Wrong directory setup, WORK_DIR: {WORK_DIR}"

def sample_SRDD(num_samples=10, seed=42):
    SRDD_path = Path(WORK_DIR) / 'SRDD/data/data_attribute_format.csv'
    SRDD_keys = ['Name', 'Description', 'Category']
    assert SRDD_path.exists(), f"SRDD file {SRDD_path} does not exist."
    with open(SRDD_path, 'r') as f:
        reader = csv.DictReader(f, fieldnames=SRDD_keys)
        next(reader)  # Skip header
        SRDD_data = [row for row in reader]
    
    random.seed(seed)
    sampled_SRDD = random.sample(SRDD_data, num_samples)
    return sampled_SRDD


processes = []
def run_SRDD_task(SRDD_data, enable_reasoning=False):
    name = SRDD_data['Name']
    description = SRDD_data['Description']
    category = SRDD_data['Category']
    # Skip if the directory already exists
    # match the regex pattern for the directory name
    warehouse_dir = Path(WORK_DIR) / 'WareHouse'
    if warehouse_dir.match(f"{name}_SRDD_{category}*"):
        print(f"Directory {name}_SRDD_{category} already exists, skipping.")
        return
    exit(1)
    cmd = f"cd {WORK_DIR} && uv run python run.py --name '{name}' --task '{description}' --org 'SRDD_{category}'"
    if enable_reasoning:
        cmd += " --enable-reasoning"
    print(f"Running command: {cmd}")
    subprocess.run(cmd, shell=True, text=True, executable="/bin/bash")

if __name__ == "__main__":
    parser = ArgumentParser(description="Run example games in parallel.")
    parser.add_argument(
        "--num_samples",
        type=int,
        default=10,
        help="Number of SRDD samples to run.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling SRDD data.",
    )
    parser.add_argument(
        "--max_concurrent_processes",
        type=int,
        default=10,
        help="Maximum number of concurrent processes to run.",
    )
    parser.add_argument(
        "--enable-reasoning",
        action="store_true",
        help="Enable reasoning for the game tasks.",
    )
    args = parser.parse_args()
    num_samples = args.num_samples
    seed = args.seed
    max_concurrent_processes = args.max_concurrent_processes
    enable_reasoning = args.enable_reasoning

    sampled_SRDD = sample_SRDD(num_samples=num_samples, seed=seed)

    with ThreadPoolExecutor(max_workers=max_concurrent_processes) as executor:
        executor.map(lambda SRDD: run_SRDD_task(SRDD, enable_reasoning), sampled_SRDD)
