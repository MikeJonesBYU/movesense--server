# Swim Sensors -- Server
This is a server that analyzes with machine learning to look for meaningful data to be sent to a mobile application.

## Installation
To install all python dependencies, run
```
pip install -r misc/requirements
```

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

More information can be found at
```
python server.py -h
```

### IOServer
If the mobile app communicates with socket.io, the IOServer can be used. To start one, run
```
python io_server.py
```
