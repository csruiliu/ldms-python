import os
import shutil
import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

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


def check_substring(main_string, sub_string):
    return main_string.find(sub_string) != -1


def refine_profile(profile_df,
                   metrics_list,
                   profile_time_unit = "ns",
                   profile_time_utc = False):
    
    profile_df['Time'] = pd.to_datetime(profile_df['timestamp'], 
                                        unit=profile_time_unit, 
                                        utc=profile_time_utc)
    
    metrics_gb = ["cpu_vmstat_mem_free", 
                  "cpu_vmstat_mem_swpd",
                  "cpu_vmstat_mem_cache"] 

    metrics_mb = ["cpu_vmstat_mem_buff"]

    for m in metrics_list:
        if m in metrics_gb:
            profile_df[metrics_descriptions.get(m)] = profile_df[m] / 1.0e+6
        elif m in metrics_mb:
            profile_df[metrics_descriptions.get(m)] = profile_df[m] / 1.0e+3
        else:
            profile_df[metrics_descriptions.get(m)] = profile_df[m]

    return profile_df


def plot_job(profile_data, outpath, target_metric, plot_format):
    fig, ax = plt.subplots(figsize=(36,20))
    sns.set_context('poster')
    
    if target_metric == "cpu_vmstat_cpu_id":
        ax.set_ylim(0, 110)
    elif target_metric == "cpu_vmstat_mem_free":
        ax.set_ylim(0, 550)
    elif target_metric == "cpu_vmstat_mem_buff":
        ax.set_ylim(0, 10)
    elif target_metric == "cpu_vmstat_mem_cache":
        ax.set_ylim(0, 400)
    else:
        print("No need to set ylim")

    sns.lineplot(x="Time",
                 y=metrics_descriptions.get(target_metric), 
                 hue="hostname",
                 data=profile_data)
    
    # plt.rcParams.update({'font.size': 24})
    # plt.xticks(rotation=30, fontsize=24)
    plt.xticks(fontsize=36)
    plt.yticks(fontsize=36)

    plt.xlabel('Date and Time', fontsize=48)
    plt.ylabel(metrics_descriptions.get(target_metric), fontsize=48)
    
    # plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d-%y %H:%M'))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

    plt.savefig(outpath + "." + plot_format, format=plot_format, bbox_inches='tight', pad_inches=0.05)
    

def main():
    ###################################
    # get all parameters
    ###################################
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--parquet_path', action='store', type=str,
                        help='indicate the profiled parquet file for analysis')
    parser.add_argument('-o', '--output_dir', action='store', type=str,
                        help='indicate the output directory to store profiled results')
    parser.add_argument('-tu', '--profile_time_unit', action='store', type=str, choices=["ns", "s"],
                        help='indicate the time unit for profiling')
    parser.add_argument('-utc', '--profile_time_utc', action='store_true',
                        help='indicate if utc time format is applied')
    args = parser.parse_args()

    parquet_path = args.parquet_path
    output_dir = args.output_dir
    profile_time_unit = args.profile_time_unit
    profile_time_utc = args.profile_time_utc

    parquet_file = parquet_path.split("/")[-1]
    job_name = parquet_file.split(".")[0]
    job_info = job_name.split("-")
    job_id = job_info[0]
    profile_metric = job_info[1]

    metrics_profile_cpu = ["cpu_vmstat_mem_buff", 
                           "cpu_vmstat_io_bi", 
                           "cpu_vmstat_io_bo",
                           "cpu_vmstat_mem_free",
                           "cpu_vmstat_procs_b",
                           "cpu_vmstat_swap_so", 
                           "cpu_vmstat_mem_cache", 
                           "cpu_vmstat_swap_si"]

    metrics_profile_gpu = ["gpu_dcgm_gpu_utilization",
                           "gpu_dcgm_tensor_active",
                           "gpu_dcgm_sm_active",
                           "gpu_dcgm_fb_used", 
                           "gpu_dcgm_pcie_rx_throughput", 
                           "gpu_dcgm_pcie_tx_throughput", 
                           "gpu_dcgm_nvlink_bandwidth_total", 
                           "gpu_dcgm_fp16_active", 
                           "gpu_dcgm_fp32_active"]
    
    if profile_metric == "cpu":
        metrics_list_profile = metrics_profile_cpu
    elif profile_metric == "gpu":
        metrics_list_profile = metrics_profile_gpu
    else:
        raise ValueError("the parquet cannot be deserialized since the machine id cannot be recognized")

    profiled_df = pd.read_parquet(parquet_path, engine='pyarrow')
    
    # Profile the workflow
    df_profile_refine = refine_profile(profiled_df, 
                                       metrics_list_profile, 
                                       profile_time_unit, 
                                       profile_time_utc)
    
    job_folder = output_dir + "/" + job_id + "-" + profile_metric
    create_folder(job_folder)

    # Plot the profile data
    for m in metrics_list_profile:
        output_path = job_folder + "/" + m
        plot_job(df_profile_refine, output_path, m, "png")
        
    
if __name__=="__main__":
    main()