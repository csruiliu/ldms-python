import os
import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

import ldms_auth_client_interface as ldms
from iris_sfapi_client_credentials import client_id, private_key
from metric_dict import metrics_descriptions


def create_folder(folder_name):
    folder = Path(folder_name)
    folder.mkdir(parents=True, exist_ok=True)
    print(f"Folder '{folder_name}' created successfully!")


def client_setup():
    session = ldms.get_session(client_id, private_key)
    token = session.fetch_token()
    print(token)

    metric_list = ldms.get_metric_list(session)
    print(metric_list)
    return session 


def fetch_profile(client_session, 
                  user_id,
                  job_id,
                  machine_id,
                  metrics_list):
    response = ldms.fetch_metrics(client_session, user_id, job_id, machine_id, metrics_list)
    print(response)

    df_ldms_fetch = ldms.get_result(client_session, response['task_id'])

    return df_ldms_fetch


def refine_profile(profile_df,
                   metrics_list,
                   profile_time_unit = "ns",
                   profile_time_utc = False):
    
    profile_df['Time'] = pd.to_datetime(profile_df['timestamp'], 
                                        unit=profile_time_unit, 
                                        utc=profile_time_utc)
    
    metrics_kb = ["cpu_vmstat_mem_buff", 
                  "cpu_vmstat_mem_cache", 
                  "cpu_vmstat_mem_free", 
                  "cpu_vmstat_mem_swpd"] 

    for m in metrics_list:
        if m in metrics_kb:
            profile_df[metrics_descriptions.get(m)] = profile_df[m] / 1.0e+6
        else:
            profile_df[metrics_descriptions.get(m)] = profile_df[m]

    return profile_df


def plot_job(profile_data, outpath, target_metric):
    fig, ax = plt.subplots(figsize=(24,16))
    sns.set_context('poster')
    sns.lineplot(x="Time",y=metrics_descriptions.get(target_metric), 
                 hue="hostname",data=profile_data)
    plt.rcParams.update({'font.size': 24})
    plt.xticks(rotation=30, fontsize=24)
    plt.xlabel('Date-Time', fontsize=24)
    plt.ylabel(metrics_descriptions.get(target_metric), fontsize=24)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H-%M-%S'))
    
    plt.savefig(outpath + ".pdf", format='pdf', bbox_inches='tight', pad_inches=0.05)
    

def main():
    ###################################
    # get all parameters
    ###################################
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--csv_file', action='store', type=str,
                        help='indicate the csv file which contains job, user, and machine id')
    parser.add_argument('-j', '--job_id', action='store', type=str,
                        help='indicate the job id you want to profile')
    parser.add_argument('-u', '--user_id', action='store', type=str,
                        help='indicate the user id associate with job for profiling')
    parser.add_argument('-m', '--machine_id', action='store', type=str,
                        help='indicate the machine id where job run at, [cpu, gpu]')
    parser.add_argument('-tu', '--profile_time_unit', action='store', type=str, choices=["ns", "s"],
                        help='indicate the time unit for profiling')
    parser.add_argument('-utc', '--profile_time_utc', action='store', type=bool,
                        help='indicate if utc time format is applied')
    parser.add_argument('-mp', '--metric_plot', action='store', type=str,
                        help='indicate the targeted metric for plotting')
    args = parser.parse_args()

    profile_time_unit = args.profile_time_unit
    profile_time_utc = args.profile_time_utc

    metrics_profile_cpu = ["cpu_vmstat_mem_free", 
                           "cpu_vmstat_io_bi", 
                           "cpu_vmstat_io_bo"]

    metrics_profile_gpu = ["gpu_dcgm_fb_used",
                           "gpu_dcgm_gpu_utilization"]

    # setup LDMS client
    client_session = client_setup()

    if args.csv_file:
        csv_file = args.csv_file
        df_csv = pd.read_csv(csv_file)

        for index, row in df_csv.iterrows():
            job_id = row["JobIDRaw"]
            user_id = row["User"]
            machine_id = row["Host Name"]

            if machine_id == "perlmutter cpu":
                metrics_list_profile = metrics_profile_cpu
            elif machine_id == "perlmutter gpu":
                metrics_list_profile = metrics_profile_gpu
            else:
                raise Exception("Sorry, machine id is not recognized")

            print(f"Job ID: {job_id}, User ID: {user_id}, Machine ID: {machine_id}")

            try:
                df_profile = fetch_profile(client_session, user_id, job_id, machine_id, metrics_list_profile)
            except ValueError as e:
                print(f"Error processing {job_id}: {e}")
                continue

            # Profile the workflow
            df_profile_refine = refine_profile(df_profile, 
                                               metrics_list_profile, 
                                               profile_time_unit, 
                                               profile_time_utc)
        
            job_folder = "job-" + job_id
            create_folder(job_folder)

            # Plot the profile data
            for m in metrics_list_profile:
                output_path = os.getcwd() + "/" + job_folder + "/" + m
                plot_job(df_profile_refine, output_path, m)

    else: 
        job_id = args.job_id
        user_id = args.user_id
        metric_plot = args.metric_plot

        if args.machine_id == "cpu":
            machine_id = "perlmutter cpu"
            metrics_list_profile = metrics_profile_cpu
        elif args.machine_id == "gpu":
            machine_id = "perlmutter gpu"
            metrics_list_profile = metrics_profile_gpu
        else:
            raise Exception("Sorry, machine id is not recognized")

        try:
            df_profile = fetch_profile(client_session, user_id, job_id, machine_id, metrics_list_profile)
        except ValueError as e:
            print(f"Error processing {job_id}: {e}")

        # Profile the workflow
        df_profile_refine = refine_profile(df_profile, 
                                           metrics_list_profile, 
                                           profile_time_unit, 
                                           profile_time_utc)

        output_path = os.getcwd() + "/profile_results/" + job_id + "/" + metric_plot

        plot_job(df_profile_refine, output_path, metric_plot)
    
    
    
if __name__=="__main__":
    main()