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
python io_server.py
```
