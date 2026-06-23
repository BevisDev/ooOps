FROM apache/airflow:3.2.2

RUN pip install --no-cache-dir \
    airflow-clickhouse-plugin==1.7.0 \
    apache-airflow-providers-oracle==4.6.1 \
    airflow-plugin-watchdog==0.6.4
    # apache-airflow-providers-microsoft-mssql==4.6.1