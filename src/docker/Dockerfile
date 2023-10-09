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