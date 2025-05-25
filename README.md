# LDMS-Python  

This repository provides code examples and tutorials for working with the Lightweight Distributed Metric Service (LDMS) Python APIs.

1. API Examples: Sample code demonstrating how to invoke LDMS Python APIs

2. Quick Start Tutorial: A beginner-friendly guide to understanding LDMS fundamentals in this README file.

## Inovking LDMS APIs

1. **ldms_auth_client_interface.py**: wrappers for the LDMS API calls.

2. **iris_sfapi_client_credentials_template.py**: *Change the file name to `iris_sfapi_client_credentials.py` after adding the credentials*. Please set up a SF API client in Iris, save the client id and private key and copy them in the file. A 'Green' client should be sufficient for using the LDMS APIs. For IP Preset, you can select multiple values from the drop down for IP preset ranges depending on where you are running the client from, for example, if we run the client from a local computer, then you can select `Your IP`.

3. **job_profile.py**: You can add `job_id`, `user_id`, `machine id`, etc to run some demos. `job_id` can be found using Slurm. `userid` is the user that submitted the job. The `machine id` could be `perlmutter cpu` or `perlmutter gpu`. Currently, Iris has no concept of job steps. Multiple metrics may be fetched at once, this will result in only one query at the backend. Sometimes jobs are requeued, the APIs will include all restarts (different nodelist and start and end). 

4. There is a limitation on the metric list: the maximum allowed length is 10. Additionally, if errors such as "max retries exceeded with url: /list_metrics" occur repeatedly, adding a short waiting time (e.g., 1–2 seconds) between requests may help mitigate the issue.

## LDMS Tutorial

This is a quick tutorial for LDMS, which mainly focuses on high-level (or basic) understanding and LDMS client APIs usuage.  

LDMS is designed to: (1) collect metrics from a variety of sources, including system hardware, OS, network, and applications, (2) be lightweight and scalable, making it suitable for large-scale systems, (3) provide both local and distributed metric collection, and (4) allow for real-time monitoring and data storage for historical analysis.

### LDMS Daemon

LDMS daemon (`ldmsd`) is a core component in LDMS, which is in `/ldms/src/ldmsd`. As a daemon process, `ldmsd` is launched and runs all the time at the server where the jobs are submitted to. It is responsible for coordinating the collection, storage, and distribution of metrics using sampler plugins and store plugins. 

The `ldmsd` daemon is typically started with a configuration specifying:

+ Sampler plugins to load (e.g., CPU, memory, network).
+ Store plugins to define how and where metrics are stored.
+ Aggregation settings for data collected across multiple nodes.
+ Communication settings (e.g., TCP, RDMA) for interacting with other LDMS instances or clients.

The frequency at which ldmsd (the LDMS daemon) checks running jobs depends on its sampling interval, which is configured in the LDMS configuration files, such as `ldmsd_config.c`. Each sampler plugin in LDMS has a configurable sampling interval, specifying how often it collects metrics.

More configuration details about `ldmsd` can be found in `/ldms/etc` and `/ldms/src/ldmsd/ldmsd_config.c`.

### Sample Plugins

Plugins are a critical part of LDMS. The sampler plugins collect metrics from specific sources (e.g., CPU utilization, memory usage, network stats). More details can be found in `/ldms/src/sampler`.

**1. Hardware Performance Counters:**

LDMS interfaces with hardware performance counters through plugins that utilize libraries like PAPI and RAPL. 

+ PAPI (Performance Application Programming Interface): Some LDMS configurations may leverage PAPI, a widely-used library that abstracts hardware performance counters. PAPI allows LDMS to gather detailed hardware metrics without directly interacting with low-level APIs. See more details in `/ldms/src/sampler/papi/papi_sampler.c`.

+ RAPL (Running Average Power Limit): LDMS can gather energy-related metrics from Intel CPUs using RAPL counters, which provide data about energy consumption for CPUs, DRAM, and other components. See more details in `/ldms/src/sampler/rapl/rapl.c`.

**2. System Calls:**

LDMS uses system calls in several sampler plugins to interact with the underlying Linux kernel and gather system metrics directly. 

For instance, for accessing hardware performance counters, LDMS may use the `perf_event_open()` system call, which is part of the Linux perf subsystem. This is common in plugins like papi or custom hardware monitoring. Also, LDMS may use the `ioctl()` system call for interacting with specific devices or subsystems, such as collecting metrics from RDMA devices and monitoring specific hardware components.

LDMS also collects system-level metrics by reading from the `/proc` filesystem and making system calls. For example, the sampler/procstat plugin gathers CPU statistics by reading `/proc/stat`, get `/proc/meminfo` by reading `/proc/meminfo`, and geting network statistics by reading `/proc/net/dev`

### Store Plugins

Store plugins in LDMS are responsible for exporting collected metrics from the LDMS daemon to external storage systems, databases, or files for analysis and persistence. More details can be found in `/ldms/src
/store`.

There are some commonly store methods. For example, **store_csv** exports metrics to CSV files, each metric set is written as a row in a CSV file, more details in `/ldms/src/store/store_csv.c`; **store_influx** exports metrics to an InfluxDB time-series database, metrics are written as time-series data with tags for filtering, more details in `/ldms/src/store/`.


Ackknowledgement:
-----
1. Thanks for Dhruva Kulkarni from NERSC

2. LDMS (Lightweight Distributed Metric Service), https://github.com/ovis-hpc/ldms
