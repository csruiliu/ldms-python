import os
import sqlite3
import argparse
import pandas as pd
from sqlite3 import Error

# All column names in schema
col_names = [
    'Start', 'JobIDRaw', 'User', 'Account', 'QOS', 'Partition', 'ReservationId', 
    'Reservation', 'Constraints', 'Submit', 'Eligible', 'End', 'ElapsedRaw', 
    'Timelimit', 'NNodes', 'ReqCPUS', 'ReqMem', 'State', 'ExitCode', 'QueueTime'
]

# Projected columns for query, make sure `selected_cols` and `projection_query` are matched
selected_cols = ['JobIDRaw', 'User', 'Partition']
projected_cols = "JobIDRaw, User, Partition"

def create_connection(db_file):
    """ Create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to {db_file}, SQLite version: {sqlite3.sqlite_version}")
        return conn
    except Error as e:
        print(e)
    return conn


def query_jobs(db_conn, project_id, state):
    params = list()
    cursor = db_conn.cursor()

    query = f"SELECT {projected_cols} FROM jobs WHERE Account = ?"
    params.append(project_id)
    
    query += " AND State = ?"
    params.append(state)

    cursor.execute(query, params)
    results = cursor.fetchall()
    
    result_df = pd.DataFrame(results, columns=selected_cols)

    return result_df


def output_csv(query_results, project_id, output_dir, output_overwrite):
    # Creates folder if it does not exist
    if not os.path.exists(output_dir):
        print(f"{output_dir} doesn't exsit and create it")
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, f"{project_id}_jobs.csv")

    if os.path.exists(output_file):
        print("Output CSV file exists")
        if output_overwrite:
            os.remove(output_file)
            print("Remove existed CSV file")
        else:
            print("Append existed CSV file")
    else:
        print("Output CSV doesn't exist and create it")

    query_results.to_csv(output_file, index=False)
    

def main():
    ###################################
    # get all parameters
    ###################################
    parser = argparse.ArgumentParser()
    parser.add_argument('-sp', '--sqlitedb_path', action='store', type=str,
                        help='indicate the sqlite database path')
    parser.add_argument('-p', '--project_id', action='store', type=str,
                        help='indicate project id for querying jobs')
    parser.add_argument('--state', action='store', type=str, default='COMPLETED', 
                        help='indicate job state for querying (default: COMPLETED).')
    parser.add_argument('-o', '--output_dir', action='store', type=str,
                        help='indicate the output directory to store csv file')
    parser.add_argument('--output_overrwite', action='store', type=bool, default=False,
                        help='indicate the if the output csv file will be overwriten')
    args = parser.parse_args()

    sqlite_db = args.sqlitedb_path
    project_id = args.project_id
    state = args.state
    output_dir = args.output_dir
    output_overwrite = args.output_overrwite

    # Create a database connection
    conn = create_connection(sqlite_db)
    query_results = query_jobs(conn, project_id, state)
    print(query_results)
    output_csv(query_results, project_id, output_dir, output_overwrite)
    
    conn.close()


if __name__=="__main__":
    main()