import os
from datetime import datetime
import logging

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from google.cloud import storage
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator
import pandas as pd

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")

dataset_file = "yellow_tripdata_{{ execution_date.strftime(\'%Y-%m\') }}.parquet"
dataset_url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{dataset_file}"
path_to_local_home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
csv_file = dataset_file.replace('.parquet', '.csv')
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'trips_data_all')


def format_to_csv(src_file):
    if not src_file.endswith('.parquet'):
        logging.error("Can only accept source files in parquet format, for the moment")
        return
    df = pd.read_parquet(src_file)
    df.to_csv(src_file.replace('.parquet', '.csv'))

def upload_to_gcs(bucket, object_name, local_file):
    """
    Ref: https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python
    :param bucket: GCS bucket name
    :param object_name: target path & file-name
    :param local_file: source path & file-name
    :return:
    """
    # WORKAROUND to prevent timeout for files > 6 MB on 800 kbps upload speed.
    # (Ref: https://github.com/googleapis/python-storage/issues/74)
    storage.blob._MAX_MULTIPART_SIZE = 5 * 1024 * 1024  # 5 MB
    storage.blob._DEFAULT_CHUNKSIZE = 5 * 1024 * 1024  # 5 MB
    # End of Workaround

    client = storage.Client()
    bucket = client.bucket(bucket)

    blob = bucket.blob(object_name)
    blob.upload_from_filename(local_file)

with DAG(
    dag_id="data_ingestion_gcp",
    schedule_interval="0 6 2 * *",
    start_date=datetime(2021, 2, 1),
    end_date=datetime(2021, 2, 28)
) as dag:

    # download parquet file from the web to local
    download_dataset_task = BashOperator(
        task_id="download_dataset_task",
        bash_command=f"curl -sSL {dataset_url} > {path_to_local_home}/{dataset_file}"
    )

    # format parquet file to csv
    format_to_csv_task = PythonOperator(
        task_id="format_to_csv_task",
        python_callable=format_to_csv,
        op_kwargs={
            "src_file": f"{path_to_local_home}/{dataset_file}",
        },
    )

    # upload local csv file to GCS bucket under raw/ prefix
    local_to_gcs_task = PythonOperator(
        task_id="local_to_gcs_task",
        python_callable=upload_to_gcs,
        op_kwargs={
            "bucket": BUCKET,
            "object_name": f"raw/{csv_file}",
            "local_file": f"{path_to_local_home}/{csv_file}",
        },
    )

    # upload csv file from GCS bucket to BigQuery dataset (trips_data_all)
    bigquery_external_table_task = BigQueryCreateExternalTableOperator(
        task_id="bigquery_external_table_task",
        destination_project_dataset_table=f"{PROJECT_ID}.{BIGQUERY_DATASET}.external_table",
        bucket=BUCKET,
        source_objects=[f"raw/{csv_file}"],
        schema_fields=[
            {"name": "index", "type": "INT64", "mode": "REQUIRED"},
            {"name": "VendorID", "type": "INT64"},
            {"name": "tpep_pickup_datetime", "type": "TIMESTAMP"},
            {"name": "tpep_dropoff_datetime", "type": "TIMESTAMP"},
            {"name": "passenger_count", "type": "FLOAT64"},
            {"name": "trip_distance", "type": "FLOAT64"},
            {"name": "RatecodeID", "type": "FLOAT64"},
            {"name": "store_and_fwd_flag", "type": "STRING"},
            {"name": "PULocationID", "type": "INT64"},
            {"name": "DOLocationID", "type": "INT64"},
            {"name": "payment_type", "type": "INT64"},
            {"name": "fare_amount", "type": "FLOAT64"},
            {"name": "extra", "type": "FLOAT64"},
            {"name": "mta_tax", "type": "FLOAT64"},
            {"name": "tip_amount", "type": "FLOAT64"},
            {"name": "tolls_amount", "type": "FLOAT64"},
            {"name": "improvement_surcharge", "type": "FLOAT64"},
            {"name": "total_amount", "type": "FLOAT64"},
            {"name": "congestion_surcharge", "type": "FLOAT64"},
            {"name": "airport_fee", "type": "FLOAT64"}
        ],
        skip_leading_rows=1
    )           

    download_dataset_task >> format_to_csv_task >> local_to_gcs_task >> bigquery_external_table_task