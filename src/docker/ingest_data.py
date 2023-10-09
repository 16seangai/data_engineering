#!/usr/bin/env python
# coding: utf-8

from sqlalchemy import create_engine
import pandas as pd
import pyarrow.parquet as pq
from time import time
import argparse
import os

def main(params):
    user = params.user
    password = params.password
    host = params.host
    port = params.port
    db = params.db
    table_name = params.table_name
    url = params.url
    parquet_name = 'taxi_trip_data.parquet'

    os.system(f"wget {url} -O {parquet_name}")

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

    # Create table with no rows. Replace table if it already exists in the database
    df = pd.read_parquet(parquet_name)
    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')

    # Insert data from dataframe into postgres database in batches of 100000 rows
    taxi_data = pq.ParquetFile(parquet_name)

    for batch in taxi_data.iter_batches(batch_size=100000):
        t_start = time()
        batch_df = batch.to_pandas()
        batch_df.to_sql(name=table_name, con=engine, if_exists='append')
        t_end = time()
        print('inserted another chunk..., took %.3f second' % (t_end - t_start))
  
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Ingest parquet data to Postgres')

    parser.add_argument('--user', help='user name for postgres')
    parser.add_argument('--password', help='password for postgres')
    parser.add_argument('--host', help='host for postgres')
    parser.add_argument('--port', help='port for postgres')
    parser.add_argument('--db', help='database name for postgres')
    parser.add_argument('--table-name', help='name of the table where we wil write the results to')
    parser.add_argument('--url', help='url of the parquet file')

    args = parser.parse_args()

    main(args)