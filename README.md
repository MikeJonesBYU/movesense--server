# Swim Sensors -- Server
This is a server that analyzes with machine learning to look for meaningful data to be sent to a mobile application.

## Installation
### Python
To install all python dependencies, run
```
pip install -r misc/requirements
```
### Database
This app does require a database support with sqlalchemy. Create a db_settings.py file to instruct the server how to connect to the database (following the example provided). Hypothetically any database sqlalchemy can interact with can be used, but the default for this project is postgres. To view more information about how to install postgres, visit [PostgreSQL's site](https://www.postgresql.org/download/).

## Usage
### Base Server
To start a basic server on the default port, run
```
python server.py
```

A port can be specified with
```
python server.py -p [port]
```

More information can be viewed with the command
```
python server.py -h
```

### IOServer
If the mobile app communicates with socket.io, the IOServer can be used. To start one, run
```
python io_server.py -p 8000
```
The server port defaults to port 80 if none is specified. To run on port 80, however, you need to run as root:
```
sudo python io_server.py
```


### Helpful Commands on the AWS Server
There are a few bash commands that have been added to the AWS server.

To list the current server instances running:
```
server_status
```

To start a server in the background:
```
server_start
```

To clear the database
```
clear_db
```

### Database Interaction
Data sent from the app to the server is stored in a PostgreSQL database. To view the data you need to connect to the database and query the data.

To connect to the database:
```
sudo -u postgres psql movesense_db
```
This lets you interact with the movesense_db using psql.
Alternatively, if you log in to psql:
```
sudo -u postgres psql
```
You can then connect with:
```
\c movesense_db
```


#### Helpful psql Commands

```
\d
```
Lists the tables in the database.

```

```
select * from {table_name};
```
Lists all entries from the table specified.

```
select column_name from information_schema.columns where table_name = '{table_name}';
```
Lists all column names from the specified table.

```
\h
```
Lists other query commands.

```
\?
```
Lists other psql commands

```
\q
```
Exits psql