import pandas as pd
import matplotlib.pyplot as plt
import argparse
import sys
import io # Used to read string as file-like object

prefill_tokens_per_second = 1500

def plot_token_growth(file_path: str, out_file_path: str):
    """
    Loads token data from a CSV file and generates a single line plot
    showing the progression of total tokens (from prompt to total) over time.

    Args:
        file_path (str): The path to the CSV file containing token data.
    """
    # --- 1. Data Loading and Initial Correction ---
    try:
        with open(file_path, 'r') as f:
            file_content = f.read()
        
        # Correct the invalid month '25' to '05' assuming a typo.
        # This is a specific fix for your provided data's date format.
        file_content = file_content.replace('2025-25-', '2025-05-')
        
        # Load the corrected data into a pandas DataFrame.
        df = pd.read_csv(io.StringIO(file_content))

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        sys.exit(1) # Exit with an error code
    except pd.errors.EmptyDataError:
        print(f"Error: The CSV file '{file_path}' is empty or contains only headers.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading or processing the CSV: {e}")
        sys.exit(1)

    # --- 2. Data Preprocessing ---
    # Convert time columns to datetime objects for proper time-series plotting.
    # 'errors=coerce' will turn unparseable dates into NaT (Not a Time),
    # preventing errors and allowing us to drop invalid rows.
    df['send_time'] = pd.to_datetime(df['send_time'], errors='coerce')
    df['recv_time'] = pd.to_datetime(df['recv_time'], errors='coerce')

    # Find the minimum timestamp among all send_time and recv_time
    min_time = min(df['send_time'].min(), df['recv_time'].min())

    # Convert send_time and recv_time to seconds (float) since min_time
    df['send_time'] = (df['send_time'] - min_time).dt.total_seconds()
    df['recv_time'] = (df['recv_time'] - min_time).dt.total_seconds()
    # Drop rows where datetime conversion failed (if any)
    df.dropna(subset=['send_time', 'recv_time'], inplace=True)
    
    if df.empty:
        print("After processing, no valid time-series data remains. Exiting.")
        sys.exit(0) # Exit gracefully

    # Sort the DataFrame by receive time to ensure the plot is chronological.
    df = df.sort_values(by='recv_time').reset_index(drop=True)

    # --- 3. Prepare Data for Single Line Plot ---
    # We need to construct a new set of (x, y) coordinates for the single line.
    # For each row/interaction, we will add two points:
    # 1. (send_time, prompt_tokens) - The state at the start of the interaction.
    # 2. (recv_time, total_tokens) - The state at the end of the interaction.
    
    send_times = df['send_time']
    plot_x_coords = []
    plot_y_coords = []

    for index, row in df.iterrows():
        # Point 1: Start of interaction
        plot_x_coords.append(row['send_time'])
        plot_y_coords.append(0)
        # Add a point at the estimated time when prompt tokens are finished being processed
        # prompt_time = row['send_time'] + pd.to_timedelta(row['prompt_tokens'] / prefill_tokens_per_second, unit='s')
        prompt_time = row['send_time'] + row['prompt_tokens'] / prefill_tokens_per_second
        plot_x_coords.append(prompt_time)
        plot_y_coords.append(row['prompt_tokens'])
        
        # Point 2: End of interaction
        plot_x_coords.append(row['recv_time'])
        plot_y_coords.append(row['total_tokens'])
        
        # Optional: Add an "intermediate" point for visual clarity between distinct interactions.
        # If the next interaction starts significantly later, this helps visualize the drop.
        # This will create a vertical drop from total_tokens of current interaction
        # to prompt_tokens of next interaction.
        if index < len(df) - 1:
            next_row = df.iloc[index + 1]
            # Add a point at the recv_time of current row with next prompt_tokens
            # This creates a "jump" or "reset" in token count between interactions
            # from the end of one interaction to the start of the next.
            plot_x_coords.append(row['recv_time'])
            plot_y_coords.append(0) # Value drops to the next prompt
            
            # Add a point at the send_time of next row with next prompt_tokens
            # To ensure the line remains flat until the next interaction starts
            # plot_x_coords.append(next_row['send_time'])
            # plot_y_coords.append(next_row['prompt_tokens'])

    # --- 4. Plotting ---
    plt.figure(figsize=(16, 8)) # Wider figure for better time axis readability

    plt.plot(plot_x_coords, plot_y_coords, 
             linestyle='-', color='blue', linewidth=2,
             label='Total Tokens (Prompt to Completion)')
    
    # Draw veritcal lines with send_times to indicate interaction boundaries
    for send_time in send_times:
        plt.axvline(x=send_time, color='gray', linestyle='--', alpha=0.3)

    plt.title('Total Tokens Over Time (Interaction Growth and Serialization)', fontsize=18)
    plt.xlabel('Time (s)', fontsize=14)
    plt.ylabel('Token Count', fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, linestyle='-', color='black', alpha=0.7)
    plt.gcf().autofmt_xdate() # Automatically format x-axis labels for dates
    plt.tight_layout() # Adjust layout to prevent labels overlapping
    plt.savefig(out_file_path)
    plt.close()

    # --- 5. Data Summary (Optional, but good for debugging/understanding) ---
    print("\n--- Data Head (After Processing) ---")
    print(df[['recv_time', 'prompt_tokens', 'completion_tokens', 'total_tokens']].head())
    print("\n--- Plotting Data Points Summary (First few) ---")
    # For a large dataset, printing all points might be excessive.
    # print(pd.DataFrame({'Time': plot_x_coords, 'Tokens': plot_y_coords}).head(10))

def main():
    """
    Parses command-line arguments and calls the plotting function.
    """
    parser = argparse.ArgumentParser(
        description="Generate a single line graph of total token progression over time from a CSV file.",
        formatter_class=argparse.RawTextHelpFormatter # For multiline help messages
    )
    parser.add_argument(
        "--csv_file",
        type=str,
        help="""Path to the CSV file containing token data.
Expected columns: role, phase_name, turn, prompt_tokens, 
completion_tokens, total_tokens, send_time, recv_time.

Example usage:
  python plot_tokens_single_line.py token_data.csv"""
    )

    args = parser.parse_args()

    csv_file = args.csv_file
    out_file_path = csv_file.replace('.csv', '.pdf')

    # Call the plotting function with the provided file path
    plot_token_growth(csv_file, out_file_path=out_file_path)

# This ensures that main() is called only when the script is executed directly
if __name__ == "__main__":
    main()