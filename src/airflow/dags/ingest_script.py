from time import time

import pandas as pd
from sqlalchemy import create_engine
import pyarrow.parquet as pq

def ingest_callable(user, password, host, port, db, table_name, parquet_file, execution_date):
    print(table_name, parquet_file, execution_date)

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')
    engine.connect()

    print('connection established successfully, inserting data...')

    df = pd.read_parquet(parquet_file)
    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')

    # Insert data from dataframe into postgres database in batches of 100000 rows
    taxi_data = pq.ParquetFile(parquet_file)

    for batch in taxi_data.iter_batches(batch_size=100000):
        t_start = time()
        batch_df = batch.to_pandas()
        batch_df.to_sql(name=table_name, con=engine, if_exists='append')
        t_end = time()
        print('inserted another chunk..., took %.3f second' % (t_end - t_start))
