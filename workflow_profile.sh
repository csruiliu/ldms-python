#!/bin/bash

# Check if the user provided a CSV file as an argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <csv_file>"
    exit 1
fi

CSV_FILE="$1"
RESULTS_FOLDER="profile_results"

# Check if the file exists
if [ ! -f "$CSV_FILE" ]; then
    echo "Error: File '$CSV_FILE' not found!"
    exit 1
fi

# Read the CSV file line by line (skipping the header)
tail -n +2 "$CSV_FILE" | while IFS=, read -r job user machine misc
do
    echo "[Bash] Processing: $job, $user, $machine"
    
    MACHINE_REFINE=${machine//\"/}
    python3 workflow_profile.py -j "$job" -u "$user" -m "$MACHINE_REFINE" -tu "s" -utc "True" -pf "png"
done

