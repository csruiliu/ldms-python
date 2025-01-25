# LDMS Tutorial

This is a quick tutorial for LDMS (Lightweight Distributed Metric Service), which mainly focuses on how to use LDMS client APIs.  

1. **ldms_auth_client_interface.py**: wrappers for the LDMS API calls.

2. **iris_sfapi_client_credentials_template.py**: *Change the file name to `iris_sfapi_client_credentials.py` after adding the credentials*. Please set up a SF API client in Iris, save the client id and private key and copy them in the file. A 'Green' client should be sufficient for using the LDMS APIs. For IP Preset, you can select multiple values from the drop down for IP preset ranges depending on where you are running the client from, for example, if we run the client from a local computer, then you can select `Your IP`.

3. **demo_template.py**: You can add `job_id`, `user_id`, `machine id`, etc to run some demos. `job_id` can be found using Slurm. `userid` is the user that submitted the job. The It seems that `machine id` could be `perlmutter cpu` or `perlmutter gpu`. Currently, Iris has no concept of job steps. Multiple metrics may be fetched at once, this will result in only one query at the backend. Sometimes jobs are requeued, the APIs will include all restarts (different nodelist and start and end). 


Ackknowledgement:
-----
1. Thanks for Dhruva Kulkarni from NERSC who helped a lot for this tutorial.

2. LDMS (Lightweight Distributed Metric Service), https://github.com/ovis-hpc/ldms
