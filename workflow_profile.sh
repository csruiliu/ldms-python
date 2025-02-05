#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: $0 -i input_csv -o output_dir"
    exit 1
}

# Parse command-line arguments using getopts
while getopts ":i:o:" opt; do
    case "${opt}" in
        i)
            CSV_FILE=${OPTARG}
            ;;
        o)
            RESULTS_FOLDER=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done

# Ensure both input CSV file and output directory are provided
if [ -z "${INPUT_CSV}" ] || [ -z "${OUTPUT_DIR}" ]; then
    echo "Error: Both input CSV file and output directory must be specified."
    usage
fi

# Check if the folder exists
if [ ! -d "$RESULTS_FOLDER" ]; then
    echo "Directory '$RESULTS_FOLDER' does not exist. Creating now..."
    mkdir -p "$RESULTS_FOLDER"
    if [ $? -eq 0 ]; then
        echo "Directory '$RESULTS_FOLDER' created successfully."
    else
        echo "Failed to create directory '$RESULTS_FOLDER'."
        exit 1
    fi
else
    echo "Directory '$RESULTS_FOLDER' already exists."
fi

# Check if the file exists
if [ ! -f "$CSV_FILE" ]; then
    echo "Error: File '$CSV_FILE' not found!"
    exit 1
fi

start_time=$(date +%s)

# Read the CSV file line by line (skipping the header)
tail -n +2 "$CSV_FILE" | while IFS=, read -r job user machine misc
do
    echo "[Bash] Processing: $job, $user, $machine"
    
    MACHINE_REFINE=${machine//\"/}
    python3 workflow_profile.py -j "$job" -u "$user" -m "$MACHINE_REFINE" -tu "s" -utc "True" -pf "png"
done

end_time=$(date +%s)
duration=$((end_time - start_time))

# Convert seconds into hours, minutes, and seconds
hours=$((duration / 3600))
minutes=$(((duration % 3600) / 60))
seconds=$((duration % 60))

echo "Total duration: ${hours}h ${minutes}m ${seconds}s"