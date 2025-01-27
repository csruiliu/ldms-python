import os
import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import ldms_auth_client_interface as ldms
from iris_sfapi_client_credentials import client_id, private_key
from metric_dict import metrics_descriptions


def client_setup():
    session = ldms.get_session(client_id, private_key)
    token = session.fetch_token()
    print(token)

    metric_list = ldms.get_metric_list(session)
    print(metric_list)
    return session 


def profile_job(session, 
                user_id, 
                job_id, 
                machine_id, 
                metrics_list,
                profile_time_unit = "ns",
                profile_time_utc = False):
    response = ldms.fetch_metrics(session, user_id, job_id, machine_id, metrics_list)
    print(response)

    try:
        df_profile = ldms.get_result(session, response['task_id'])
    except ValueError as e:
        print(e)
    
    df_profile['Time'] = pd.to_datetime(df_profile['timestamp'], 
                                        unit=profile_time_unit, 
                                        utc=profile_time_utc)
    
    for m in metrics_list:
        if m == "cpu_vmstat_mem_free":
            df_profile[metrics_descriptions.get(m)] = df_profile[m]/1.0e+6
        else:
            df_profile[metrics_descriptions.get(m)] = df_profile[m]

    df_profile.to_csv("sss.csv", index=False)

    return df_profile


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
    
    plt.savefig(outpath, format='pdf', bbox_inches='tight', pad_inches=0.05)
    

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
                        help='indicate the machine id where job run at')
    parser.add_argument('-tu', '--profile_time_unit', action='store', type=str, choices=["ns", "s"],
                        help='indicate the time unit for profiling')
    parser.add_argument('-utc', '--profile_time_utc', action='store', type=bool,
                        help='indicate if utc time format is applied')
    parser.add_argument('-mp', '--metric_plot', action='store', type=str,
                        help='indicate the targeted metric for plotting')
    
    metric_plot = "cpu_vmstat_io_bi"
    args = parser.parse_args()

    job_id = args.job_id
    user_id = args.user_id
    profile_time_unit = args.profile_time_unit
    profile_time_utc = args.profile_time_utc
    metric_plot = args.metric_plot

    if args.machine_id == "cpu":
        machine_id = "perlmutter cpu"
    elif args.machine_id == "gpu":
        machine_id = "perlmutter gpu"
    else:
        raise Exception("Machine ID is not recognized")

    output_path = os.getcwd() + "/ldms-" + job_id + ".pdf"

    metrics_list = ["cpu_vmstat_cpu_us","cpu_vmstat_cpu_sy","cpu_vmstat_mem_free", "cpu_vmstat_io_bi", "cpu_vmstat_io_bo"]

    # setup LDMS client
    client_session = client_setup()
    # Profile the workflow
    profile_data = profile_job(client_session, 
                               user_id, 
                               job_id, 
                               machine_id, 
                               metrics_list, 
                               profile_time_unit, 
                               profile_time_utc)
    # Plot the profile data
    plot_job(profile_data, output_path, metric_plot)
    
    
if __name__=="__main__":
    main()