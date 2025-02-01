import os
import shutil
import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

import ldms_auth_client_interface as ldms
from iris_sfapi_client_credentials import client_id, private_key
from metric_dict import metrics_descriptions


def create_folder(folder_path):
    '''
    # Delete the folder if it exists and create a new one."""
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path)
    '''
    # Creates folder if it does not exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


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

    job_id = args.job_id
    user_id = args.user_id
    machine_id = args.machine_id
    profile_time_unit = args.profile_time_unit
    profile_time_utc = args.profile_time_utc
    metric_plot = args.metric_plot

    metrics_profile_cpu = ["cpu_vmstat_cpu_id", 
                           "cpu_vmstat_io_bi", 
                           "cpu_vmstat_io_bo",
                           "cpu_vmstat_mem_buff",
                           "cpu_vmstat_mem_swpd",
                           "cpu_vmstat_mem_free",
                           "cpu_vmstat_procs_r", 
                           "cpu_vmstat_system_in", 
                           "cpu_vmstat_system_cs"]

    metrics_profile_gpu = ["gpu_dcgm_gpu_utilization",
                           "gpu_dcgm_tensor_active",
                           "gpu_dcgm_sm_active",
                           "gpu_dcgm_fb_used", 
                           "gpu_dcgm_pcie_rx_throughput", 
                           "gpu_dcgm_pcie_tx_throughput", 
                           "gpu_dcgm_nvlink_bandwidth_total", 
                           "gpu_dcgm_fp16_active", 
                           "gpu_dcgm_fp32_active", 
                           "gpu_dcgm_fp64_active"]
    
    print(f"[Python] Processing: {job_id}, {user_id}, {machine_id}")
    
    if machine_id == "perlmutter cpu":
        metrics_list_profile = metrics_profile_cpu
    elif machine_id == "perlmutter gpu":
        metrics_list_profile = metrics_profile_gpu
    else:
        raise Exception("Sorry, machine id is not recognized")
    
    # setup LDMS client
    client_session = client_setup()

    try:
        df_profile = fetch_profile(client_session, user_id, job_id, machine_id, metrics_list_profile)
    except ValueError as e:
        print(f"Error processing {job_id}: {e}")

    # Profile the workflow
    df_profile_refine = refine_profile(df_profile, 
                                       metrics_list_profile, 
                                       profile_time_unit, 
                                       profile_time_utc)
    
    job_folder = os.getcwd() + "/profile_results/" + job_id + "-" + machine_id.split()[-1]
    create_folder(job_folder)

    # Plot the profile data
    if metric_plot is None:
        for m in metrics_list_profile:
            output_path = job_folder + "/" + m
            plot_job(df_profile_refine, output_path, m)
    else:
        output_path = job_folder + "/" + metric_plot
        plot_job(df_profile_refine, output_path, metric_plot)
    
    
if __name__=="__main__":
    main()