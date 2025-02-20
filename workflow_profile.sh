#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: $0 -i input_csv -o output_dir -m [cpu, gpu, <single_metric>]"
    exit 1
}

# Parse command-line arguments using getopts
while getopts ":i:o:m:" opt; do
    case "${opt}" in
        i)
            CSV_FILE=${OPTARG}
            ;;
        o)
            RESULTS_FOLDER=${OPTARG}
            ;;
        m)
            METRIC=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done

# Ensure both input CSV file and output directory are provided
if [ -z "${CSV_FILE}" ] || [ -z "${RESULTS_FOLDER}" ]; then
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
    if [ "$METRIC" == "cpu" ]; then
        python3 workflow_profile.py -j "$job" -u "$user" -m "$MACHINE_REFINE" -o "$RESULTS_FOLDER" -tu "s" -pf "png" --metric_cpu -utc
    elif [ "$METRIC" == "gpu" ]; then 
        python3 workflow_profile.py -j "$job" -u "$user" -m "$MACHINE_REFINE" -o "$RESULTS_FOLDER" -tu "s" -pf "png" --metric_gpu -utc
    else 
        python3 workflow_profile.py -j "$job" -u "$user" -m "$MACHINE_REFINE" -o "$RESULTS_FOLDER" -tu "s" -pf "png" --metric_single "$METRIC" -utc
    fi

    JOB_FOLDER="$RESULTS_FOLDER/$job-$METRIC"
    # Check if the folder is empty
    if [ -z "$(ls -A $JOB_FOLDER)" ]; then
        # If the folder is empty, delete it
        rmdir $JOB_FOLDER
        if [ $? -eq 0 ]; then
            echo "Folder $JOB_FOLDER is empty, no profiled result, and has been deleted."
        else
            echo "Error: Failed to delete directory"
        fi
    fi
    # add some gap between any two requests to avoid some potential internal rate limit
    sleep 2
done

end_time=$(date +%s)
duration=$((end_time - start_time))

# Convert seconds into hours, minutes, and seconds
hours=$((duration / 3600))
minutes=$(((duration % 3600) / 60))
seconds=$((duration % 60))

echo "Total duration: ${hours}h ${minutes}m ${seconds}s"