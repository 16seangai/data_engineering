# Data Engineering

> Links to notes organized by subject/technology. Numbers before subsection titles indicate order
of study, gradually building towards creating a data pipeline orchestrated by Airflow which runs each month
and does the following:
  1. Downloads NYC taxi data for the previous month from the web in parquet format
  2. Converts the parquet file to csv
  3. Uploads the csv file to a GCS (Google Cloud Storage) bucket
  4. Creates a dataset in BigQuery using the csv file from the GCS bucket

[Docker](../notes/docker.md)

[Postgres](../notes/postgres.md)

[GCP](../notes/gcp.md)

[Airflow](../notes/airflow.md)