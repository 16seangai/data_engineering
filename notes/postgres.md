# Postgres

## 5. Quickstart w/Docker

- Run Postgres database in Docker container

```bash
docker run -it \
	# set environment variable for db username
	-e POSTGRES_USER="root" \
	# set envirnoment variable for db password
	-e POSTGRES_PASSWORD="root" \
	# set environment variable for database name
	-e POSTGRES_DB="ny_taxi" \
	# map folder on host machine (ny_taxi_postgres_data) to folder in container to
	# store db data. if we restart container, postgres data will not be lost
	-v $PWD/ny_taxi_postgres_data:/var/lib/postgresql/data \
	# map port from host machine to port in container
	-p 5432:5432 \
	postgres:13
```

- Test connection to database using `pgcli`

```bash
# install pgcli and postgresql
brew install pgcli

# connect to db
pgcli -h localhost -p 5432 -u root -d ny_taxi
```

## 6. Ingesting Data to Postgres w/Python on Jupyter

- Run Jupyter

```bash
jupyter notebook
```

- Download the taxi data as .parquet

```bash
wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2021-01.parquet
```

- Jupyter Notebook to insert data from .parquet file to Postgres database

```python
#!/usr/bin/env python
# coding: utf-8

# In[1]:

import pandas as pd

# In[2]:

pd.__version__

# In[7]:

# read data from parquet file to pandas dataframe
df = pd.read_parquet('yellow_tripdata_2021-01.parquet')

# In[12]:

# import SQLAlchemy to access and manage SQL databases using Python
from sqlalchemy import create_engine
engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')

# In[13]:

# Print the DDL (language used for creating and modifying database objects such as tables, users, etc.)
# syntax for creating a new database table to store taxi data using schema inferred from dataframe
print(pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine))

# In[14]:

# Create table with no rows. Replace table if it already exists in the database
df.head(n=0).to_sql(name='yellow_taxi_data', con=engine, if_exists='replace')

# In[16]:

# Insert data from dataframe into postgres database, 100000 rows at a time
import pyarrow.parquet as pq
from time import time

taxi_data = pq.ParquetFile('yellow_tripdata_2021-01.parquet')

for batch in taxi_data.iter_batches(batch_size=100000):
    t_start = time()
    batch_df = batch.to_pandas()
    batch_df.to_sql(name='yellow_taxi_data', con=engine, if_exists='append')
    t_end = time()
    print('inserted another chunk..., took %.3f second' % (t_end - t_start))
```

## 7. Interact with Postgres database w/pgAdmin GUI

- Run pgAdmin in docker image

```bash
docker run it \
	-e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
	-e PGADMIN_DEFAULT_PASSWORD="root" \
	# map port on host machine (8080) to port on container (80)
	# pgAdmin listening for requests to port 80 on the container
	# requests to port 8080 on host machine will be forwarded to
	# port 80 on the container
	-p 8080:80 \
	dpage/pgadmin4
```

- Connect pgAdmin to Postgres database by putting both containers in the same network (localhost doesn’t work because localhost in pgAdmin container refers to the container itself)
    
    ```bash
    # create network
    docker network create pg-network
    
    # restart postgres container in pg-network and add name as
    # pg-database so pgadmin can connect to it
    docker run -it \
    	-e POSTGRES_USER="root" \
    	-e POSTGRES_PASSWORD="root" \
    	-e POSTGRES_DB="ny_taxi" \
    	-v $PWD/ny_taxi_postgres_data:/var/lib/postgresql/data \
    	-p 5432:5432 \
    	--network=pg-network \
    	--name pg-database \
    	postgres:13
    
    # restart pgadmin container in pg-network
    docker run -it \
    	-e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
    	-e PGADMIN_DEFAULT_PASSWORD="root" \
    	-p 8080:80 \
    	--network=pg-network \
    	dpage/pgadmin4
    ```
    
- Click “Add New Server” to connect to database
    
    ![pgAdmin_connect.png](../notes/Screenshots/pgAdmin_connect.png)
    

## 8. Add Jupyter Upload Data Script to Data Pipeline Container

- Convert Jupyter notebook which uploads 2021 yellow taxi data to Postgres database to a Python script

```bash
jupyter nbconvert --to=script upload-data.ipynb
```

- Edit the script to remove unnecessary cells, comments
    - Parse Postgres details and parquet url as arguments
    - Download the parquet file from the specified url

```python
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
```

- Update Dockerfile to install dependencies for Python script and run updated script when container starts

```docker
# set the base image
FROM python:3.9

# install pandas library
RUN apt-get install wget
RUN pip install pandas sqlalchemy psycopg2 pyarrow

# specify the directory in the container filesystem where files will be copied
# to from our local machine
WORKDIR /app

# copy the Python file from our current working directory to the container’s
# filesystem
COPY ingest_data.py ingest_data.py

# specify command to run when container is started
ENTRYPOINT [ "python", "ingest_data.py" ]
```

- Rebuild Dockerfile into Docker image named taxi_ingest with v001 tag

```bash
docker build -t taxi_ingest:v001 .
```

- Run the Docker image to ingest data

```bash
docker run -it \
	--network=pg-network \
	taxi_ingest:v001 \
		# in production, better to keep user and password in env variables
		--user root \
		--password root \
		# in production, this would be url to a db in the cloud, for example
		--host pg-database \
		--port 5432 \
		--db ny_taxi \
		--table-name yellow_taxi_trips \
		--url https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2021-01.parquet
```

## 9. [Docker Compose to Coordinate Containers](https://www.notion.so/Docker-84975122475b43b7bc5a91e760c55400?pvs=21)