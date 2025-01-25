import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import ldms_auth_client_interface as ldms
from iris_sfapi_client_credentials import client_id, private_key


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
        df_profile = ldms.get_result(session,response['task_id'])
    except ValueError as e:
        print(e)
    
    df_profile['Time'] = pd.to_datetime(df_profile['timestamp'], unit=profile_time_unit, utc=profile_time_utc)

    df_profile['GB free'] = df_profile['cpu_vmstat_mem_free']/1.0e+6

    return df_profile


def plot_job(profile_data, outpath):
    fig, ax = plt.subplots(figsize=(24,16))
    sns.set_context('poster')
    sns.lineplot(x="Time",y='GB free',hue="hostname",data=profile_data)
    plt.rcParams.update({'font.size': 24})
    plt.xticks(rotation=30, fontsize=24)
    plt.xlabel('Date-Time', fontsize=24)
    plt.ylabel('Free Mem (GB)', fontsize=24)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H-%M-%S'))
    
    plt.savefig(outpath, format='pdf', bbox_inches='tight', pad_inches=0.05)
    

def main():
    # setup LDMS client
    client_session = client_setup()

    # Parameters for Demo 1
    machine_id = "perlmutter cpu"
    user_id = "xxxxxxxx"
    job_id = "26439169"
    output_path = "/home/ruiliu/Develop/nersc/ldms/ldms-" + job_id + ".pdf"
    metrics_list = ["cpu_vmstat_cpu_us","cpu_vmstat_cpu_sy","cpu_vmstat_mem_free"]

    profile_data = profile_job(client_session, user_id, job_id, machine_id, metrics_list)
    plot_job(profile_data, output_path)

    # Parameters for Demo 2
    machine_id = 'perlmutter gpu'
    user_id = 'xxxxxxxx'
    job_id = '20092775'
    output_path = "/home/ruiliu/Develop/nersc/ldms/ldms-" + job_id + ".pdf"
    metrics_list = ['gpu_dcgm_fb_free','gpu_dcgm_gpu_temp']

    profile_data = profile_job(client_session, user_id, job_id, machine_id, metrics_list, 
                               profile_time_unit="s", profile_time_utc = True)
    plot_job(profile_data, output_path)
    

if __name__=="__main__":
    main()