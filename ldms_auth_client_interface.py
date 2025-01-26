from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc7523 import PrivateKeyJWT
from requests.exceptions import HTTPError

import pandas as pd
import io
import time
import json


token_url = "https://oidc.nersc.gov/c2id/token"
server_url = "https://ldmsapi.nersc.gov"

def get_session(client_id, private_key):
    session = OAuth2Session(
        client_id, 
        private_key, 
        PrivateKeyJWT(token_url),
        grant_type="client_credentials",
        token_endpoint=token_url
    )
    return session

def get_metric_list(session):
    try:
        response=session.get(server_url+"/list_metrics")
        response.raise_for_status()
        return response.json()
    except HTTPError as http_err:
        print(f"HTTP error occurred") 
        return response.json()
    except Exception as err:
        print(f"error: {err}")

def fetch_generic(session,nodelist_list,start_time_list,end_time_list,sampler_metrics_list,fmt,cols):
    post_data = {
        "nodelist_list" : nodelist_list,
        "sampler_metrics_list" : sampler_metrics_list,
        "start_time_list" : start_time_list,
        "end_time_list" : end_time_list,
        "fmt" : fmt,
        "cols": cols
    }
    try:
        response=session.post(server_url+"/fetch_generic",json=post_data)
        response.raise_for_status()
        return response.json()
    except HTTPError as http_err:
        print(f"HTTP error occurred {http_err}") 
    except Exception as err:
        print(f"error: {err}")
        
def fetch_metrics(session,userid,jobid,machine_id,metrics_list):
    post_data = {
        "userid" : userid,
        "jobid" : jobid,
        "machineid" : machine_id,
        "metrics_list" : metrics_list
    }
    try:
        response=session.post(server_url+"/fetch_metrics",json=post_data)
        response.raise_for_status()
        return response.json()
    except HTTPError as http_err:
        print(f"HTTP error occurred {http_err}") 
    except Exception as err:
        print(f"error: {err}")

def poll(target,success_condition,failure_condition,retries,interval,*args,**kwargs):
    tries=0
    while tries<retries:
        response=target(*args,**kwargs)
        if success_condition(response):
            return 'success',response
        elif failure_condition(response):
            print('failure')
            return 'failure',response
        else:
            print(response.json().get('task_status'))
            time.sleep(interval)
            tries+=1
    return 'front end timed out, try again...',response

def get_result(session,taskid,retries=25,interval=1):
    status,response = poll(
        session.get,
        lambda r: r.json()['task_status']=='SUCCESS', #SUCCESS is celery code
        lambda r: r.json()['task_status']=='FAILURE', #FAILURE is celery code
        retries,
        interval,
        (server_url+"/tasks/"+taskid)
    )
    
    if status == 'success':
        #post processing for internal errors not due to celery failures
        if json.loads(response.json().get('task_result')).get('Error') is not None:
            raise ValueError(response.json().get('task_result'))
        else:
            df=pd.read_json(io.StringIO(response.json().get('task_result')),orient='split')
            df.reset_index(inplace=True)
            return df
    else:
        print(response.json())
        raise ValueError(status)