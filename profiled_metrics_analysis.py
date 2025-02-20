import os
import shutil
import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

from metric_dict import metrics_descriptions


def check_substring(main_string, sub_string):
    return main_string.find(sub_string) != -1


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


def plot_job(profile_data, outpath, target_metric, plot_format):
    fig, ax = plt.subplots(figsize=(24,16))
    sns.set_context('poster')
    sns.lineplot(x="Time",y=metrics_descriptions.get(target_metric), 
                 hue="hostname",data=profile_data)
    plt.rcParams.update({'font.size': 24})
    plt.xticks(rotation=30, fontsize=24)
    plt.xlabel('Date-Time', fontsize=24)
    plt.ylabel(metrics_descriptions.get(target_metric), fontsize=24)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H-%M-%S'))
    
    plt.savefig(outpath + "." + plot_format, format=plot_format, bbox_inches='tight', pad_inches=0.05)
    

def main():
    ###################################
    # get all parameters
    ###################################
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--parquet_file', action='store', type=str,
                        help='indicate the profiled parquet file for analysis')
    parser.add_argument('-o', '--output_dir', action='store', type=str,
                        help='indicate the output directory to store profiled results')
    args = parser.parse_args()

    parquet_file = args.parquet_file
    output_dir = args.output_dir

    metrics_profile_cpu = ["cpu_vmstat_cpu_id", 
                           "cpu_vmstat_io_bi", 
                           "cpu_vmstat_io_bo",
                           "cpu_vmstat_mem_free",
                           "cpu_vmstat_procs_b",
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
                           "gpu_dcgm_fp32_active"]
    
    job_name = parquet_file.split(parquet_file, ".")[0]
    job_info = job_name.split(job_name, "-")
    job_id = job_info[0]
    machine_id = job_info[1]

    profiled_df = pd.read_parquet(parquet_file, engine='pyarrow')
    
    if machine_id == "cpu":
        metrics_list_profile = metrics_profile_cpu
    elif machine_id == "gpu":
        metrics_list_profile = metrics_profile_gpu
    else:
        raise ValueError("the parquet cannot be deserialized since the machine id cannot be recognized")
    
    job_folder = output_dir + "/" + job_id + "-" + machine_id.split()[-1]

    # Plot the profile data
    for m in metrics_list_profile:
        output_path = job_folder + "/" + m
        plot_job(profiled_df, output_path, m, "png")
        
    
if __name__=="__main__":
    main()