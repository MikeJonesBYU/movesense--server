#!/usr/bin/env python3

##
# IO Events
##
CONNECT     = 'connect'
DISCONNECT  = 'disconnect'

###
# Client Events
###
CLIENT_DATA               = 'client_data'
ANGULAR_VELOCITY_ENTRY    = 'av_entry'
HEART_RATE_ENTRY          = 'hr_entry'
LINEAR_ACCELERATION_ENTRY = 'la_entry'
MAGNETIC_FIELD_ENTRY      = 'mf_entry'
TEMPERATURE_ENTRY         = 'te_entry'
CLIENT_REQUEST            = 'request_data'

###
# Server Events
###
SERVER_DATA      = 'server_data'
ANALYZED_DATA    = 'analyzed_data'
REQUEST_RESPONSE = 'request_response'

##
# Client Entry Keys
##
SKATER_ID   = 'skater'
SESSION_ID  = 'session'
SENSOR_ID   = 'sensor'
TIME        = 'time'
X           = 'x'
Y           = 'y'
Z           = 'z'
MEASUREMENT = 'measurement'
AVERAGE     = 'average'
DATA_TYPE   = 'data_type'

##
# Stored Data Paths
##
AV_FILE = 'data/angular_velocity.arff'
HR_FILE = 'data/heart_rate.arff'
LA_FILE = 'data/linear_acceleration.arff'
MF_FILE = 'data/magnetic_field.arff'
TE_FILE = 'data/temperature.arff'
