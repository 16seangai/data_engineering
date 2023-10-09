# Docker

## 1. Overview

- Can run applications in isolated containers
- Example containers running on same host machine:

```
Ubuntu 20.04

****************************Data pipeline****************************
- Python 3.9
- Pandas
- Postgres connection library
```

```
Postgres Database
```

```
pgAdmin
(Management tool for Postgres)
```

- Do not need to install Postgres or pgAdmin. Just need pre-configured Docker image.
- Can create a docker image for the data pipeline container and run it it on any other environment such as Google cloud or AWS batch

- Benefits of Docker
    - Reproducibility
    - Local experiments
    - Integration tests (CI/CD) — GitHub Actions, Jenkins
    - Deploy to serverless architecture

## 2. Dockerfile

- A text document that Docker reads to build images

```docker
# set the base image
FROM python:3.9

# install pandas library
RUN pip install pandas

# specify command to run when container is started
ENTRYPOINT [ "bash" ]
```

## 3. Building and Running Docker Images

- Build Docker image from `Dockerfile`

```bash
# -t option adds a tag to identify the version of the image
# test will be the name of the image and pandas will be the tag
# . specifies where the Dockerfile resides (. is current directory)
docker build -t test:pandas .
```

- Run a Docker image

```bash
# run test image, the version with tag pandas, in interactive mode (-it)
docker run -it test:pandas
```

## 4. Running a Python Script in the Container

- Specify a simple Python script to run in the Docker container
    - Create a file, `pipeline.py`

```python
import sys

# make sure that pandas installation worked correctly
import pandas as pd

# take a command-line argument (e.g. what day to process data for)
day = sys.argv[1]

# put your data processing code here

print(f'job finished successfully for day = {day}')
```

- Update our `Dockerfile`

```docker
# set the base image
FROM python:3.9

# install pandas library
RUN pip install pandas

# specify the directory in the container filesystem where files will be copied
# to from our local machine
WORKDIR /app

# copy the Python file from our current working directory to the container’s
# filesystem
COPY pipeline.py pipeline.py

# specify command to run when container is started
ENTRYPOINT [ "python", "pipeline.py" ]
```

- Rebuild `Dockerfile` to create updated Docker image

```bash
docker build -t test:pandas .
```

- Start the Docker container and process data for a given day, 2021-01-15

```bash
docker run -it test:pandas 2021-01-15 
```

## 9. Docker Compose

- Write a `docker-compose.yml` file to start and stop one or more Docker containers without needing multiple long `docker run` commands.

```yaml
services:
  pgdatabase:
    image: postgres:13
    environment:
      - POSTGRES_USER=root
      - POSTGRES_PASSWORD=root
      - POSTGRES_DB=ny_taxi
    volumes:
      - "./ny_taxi_postgres_data:/var/lib/postgresql/data:rw"
    ports:
      - "5432:5432"
  pgadmin:
    image: dpage/pgadmin4
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@admin.com
      - PGADMIN_DEFAULT_PASSWORD=root
    ports:
      - "8080:80"
```

- Start containers specified in `docker-compose.yml` file

```bash
docker-compose up
```

- Stop containers

```bash
docker-compose down
```

- Run containers in detached mode so we can keep using the terminal after running `docker-compose up`

```bash
docker-compose up -d
```