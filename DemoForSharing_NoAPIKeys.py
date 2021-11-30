import json
import requests
from requests.api import head, request
from requests.models import Response
import time
from datetime import datetime, date, timedelta
import signal
import sys

#Rebecca Johnson 2021-11-28
#Simple program to view current status of nest thermostats and how long they've been in their current state.
#Alerting if they go over a configurable amount of minutes per state.

# API Keys have been removed
ProjectID='PROJECT ID HERE'
AccessToken = ''
refreshToken = 'REFRESH TOKEN HERE'
bedroom_DeviceID='BR Device ID'
livingRoom_DeviceID='LR Device ID' 
data_DeviceResponse=""


def getAccessToken():
### RAJ 2021-11-27 Gets access token using the refresh token provided above. 
### Returns: Access Token String
### Params: None
    api_url = 'https://www.googleapis.com/oauth2/v4/token'
    param_clientID='5819746333-b511b9r9lbda0cu70ctlborossuappi9.apps.googleusercontent.com'
    param_clientSecret='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'
    param_RefreshToken = refreshToken
    param_grantType = 'refresh_token'

    response=requests.post(
        api_url,params={'client_id':param_clientID,'client_secret':param_clientSecret,'refresh_token':param_RefreshToken,'grant_type':param_grantType},
    )
    
    #print(response.status_code)
    if response.status_code==200:  
        response_json = response.json()
        #print("Success")
        #print(response_json)
        AccessToken = response_json['access_token']
        #print('Access Token: '+ AccessToken)
        return AccessToken
    else:
        print("Failure")
        return ""

def getDevicesInfo():
###Gets all device info. Results are returned in JSON Format, stored in Global - Results
###Parameters: none
###Returns: JSON Response

    RefreshTries = 0

    #print ('room: '+room)
    try:
        ##perform lookup on device id
        api_url = 'https://smartdevicemanagement.googleapis.com/v1/enterprises/'+ProjectID+'/devices/'
        #print("APIURL: "+api_url)
        response=requests.get(api_url,headers={'ContentType':'application/json', 'Authorization':'Bearer '+AccessToken})
        if response.status_code==200:
            json_response = response.json()
            return json_response
        elif response.status_code==401:
            ##unauthenticated
            ##request a new Access code, and retry. Only try once.
            if RefreshTries ==0:
                print("Retrying")
                getAccessToken()
                response=requests.get(api_url,headers={'ContentType':'application/json', 'Authorization':'bearer '+AccessToken})
                    ##get status
                json_response = response.json()
                return json_response   
            else:
                raise Exception("Unable to generate new Auth Code")   
        else: 
            raise Exception("Unable to retrieve data: Response Code: "+ str(response.status_code))

    except:
        raise Exception

def getStatus(room):
### Gets the running status of the rooms thermostat, based on the data_DeviceResponse data
### Navigating JSON with python seems to be a pain
### can get a key, but not like using xpath
### Params: room - 'bedroom' or 'livingroom'
    try:
        if room=='bedroom':
            ##get value from JSON:
            i = 0
            while i<=len(data_DeviceResponse):
                #look for the bedroom device ID. 
                if bedroom_DeviceID in data_DeviceResponse["devices"][i]["name"]:
                    ##get the status: 
                    status = data_DeviceResponse["devices"][i]["traits"]["sdm.devices.traits.ThermostatHvac"]["status"]
                i+=1
            return status
        elif room=='livingroom':
            i = 0
            while i<=len(data_DeviceResponse):
                #look for the bedroom device ID. 
                if livingRoom_DeviceID in data_DeviceResponse["devices"][i]["name"]:
                    ##get the status: 
                    status = data_DeviceResponse["devices"][i]["traits"]["sdm.devices.traits.ThermostatHvac"]["status"]
                i+=1
            return status
        else:
            raise Exception("Not a valid room")      
        

    except:
        raise Exception

def getTemp(room):
### Gets the temp of the rooms thermostat, based on the data_DeviceResponse data
### Returns temp in Celsius
### Params: room - 'bedroom' or 'livingroom'
    try:
        if room=='bedroom':
            ##get value from JSON:
            i = 0
            while i<=len(data_DeviceResponse):
                #look for the bedroom device ID. 
                if bedroom_DeviceID in data_DeviceResponse["devices"][i]["name"]:
                    ##get the status: 
                    status = data_DeviceResponse["devices"][i]["traits"]["sdm.devices.traits.Temperature"]["ambientTemperatureCelsius"]
                i+=1
            return status
        elif room=='livingroom':
            i = 0
            while i<=len(data_DeviceResponse):
                #look for the bedroom device ID. 
                if livingRoom_DeviceID in data_DeviceResponse["devices"][i]["name"]:
                    ##get the status: 
                    status = data_DeviceResponse["devices"][i]["traits"]["sdm.devices.traits.Temperature"]["ambientTemperatureCelsius"]
                i+=1
            return status
        else:
            raise Exception("Not a valid room")      
        

    except:
        raise Exception

def getTargetTemp(room):
### Gets the target temp of the rooms thermostat, based on the data_DeviceResponse data
### Returns temp in Celsius
### Params: room - 'bedroom' or 'livingroom'
    try:
        if room=='bedroom':
            ##get value from JSON:
            i = 0
            while i<=len(data_DeviceResponse):
                #look for the bedroom device ID. 
                if bedroom_DeviceID in data_DeviceResponse["devices"][i]["name"]:
                    ##get the status: 
                    status = data_DeviceResponse["devices"][i]["traits"]["sdm.devices.traits.ThermostatTemperatureSetpoint"]["heatCelsius"]
                i+=1
            return status
        elif room=='livingroom':
            i = 0
            while i<=len(data_DeviceResponse):
                #look for the bedroom device ID. 
                if livingRoom_DeviceID in data_DeviceResponse["devices"][i]["name"]:
                    ##get the status: 
                    status = data_DeviceResponse["devices"][i]["traits"]["sdm.devices.traits.ThermostatTemperatureSetpoint"]["heatCelsius"]
                i+=1
            return status
        else:
            raise Exception("Not a valid room")      
        

    except:
        raise Exception

 

###MAIN

##main loop here. While true, get the status. track initital start as status change, and each status change after that. 
##Both Bedroom and LIving room. When either status changes, update last status change time and new status. 
###wait a set number of seconds per check. Sandbox API allows up to 5 requests per minute. 
try:
    AccessToken = getAccessToken()
    time_to_wait = 20 ##lowest at sandbox level: https://developers.google.com/nest/device-access/project/limits
    max_current_state_off = timedelta (minutes=5) #maximum time to be off before alerting. Set low for testing. 
    max_current_state_on = timedelta(minutes=5) #maximum time to be on before alerting. 

    #get initial times
    currTime = datetime.now()
    
    br_changeState=datetime.now()
    lr_changeState=datetime.now()

    #get device info
    data_DeviceResponse= getDevicesInfo()

    #get initial status
    br_status = getStatus('bedroom')
    lr_status=getStatus('livingroom')

    #get target temps
    br_targetTemp = getTargetTemp('bedroom')
    br_targetTempF=(br_targetTemp*(9/5))+32
    lr_targetTemp=getTargetTemp('livingroom')
    lr_targetTempF=(lr_targetTemp*(9/5))+32

    #get current temps
    br_currentTemp = getTemp('bedroom')
    br_currentTempF=(br_currentTemp*(9/5))+32
    lr_currentTemp=getTemp('livingroom')
    lr_currentTempF=(lr_currentTemp*(9/5))+32

    ##print that info
    print ("Initial Info:")
    print("Bedroom: \t Target Temp: "+ ("{:.2f}".format(br_targetTempF)) + " Current Temp: "+ ("{:.2f}".format(br_currentTempF)) + " Status: "+ br_status)
    print("Living Room : \t Target Temp: "+ ("{:.2f}".format(lr_targetTempF)) + " Current Temp: "+ ("{:.2f}".format(lr_currentTempF)) + " Status: "+ lr_status)

    while True:
            ##infinite loop

            ##wait however long, in seconds
            time.sleep(time_to_wait)

            ##get device info
            data_DeviceResponse= getDevicesInfo()

            #get  status
            br_statusNow = getStatus('bedroom')
            lr_statusNow = getStatus('livingroom')

            ##check against current status
            if br_statusNow!=br_status:
                #update time at status
                br_changeState = datetime.now()
                br_status=br_statusNow
            if lr_statusNow!=lr_status:
                lr_changeState=datetime.now()
                lr_status=lr_statusNow

            #get target temps
            br_targetTemp = getTargetTemp('bedroom')
            if br_targetTemp!=0:
                br_targetTempF=(br_targetTemp*(9/5))+32
            
            lr_targetTemp=getTargetTemp('livingroom')
            if lr_targetTemp!=0:
                lr_targetTempF=(lr_targetTemp*(9/5))+32

            #get current temps
            br_currentTemp = getTemp('bedroom')
            if br_currentTemp!=0:
                br_currentTempF=(br_currentTemp*(9/5))+32

            lr_currentTemp=getTemp('livingroom')
            if lr_currentTemp!=0:
                lr_currentTempF=(lr_currentTemp*(9/5))+32

            #get length of time in current status
            
            br_StateTime = datetime.now() - br_changeState
            lr_StateTime = datetime.now() - lr_changeState

            ##print that info
            print("")
            print("Bedroom: \t Target Temp: "+ ("{:.2f}".format(br_targetTempF)) + " Current Temp: "+ ("{:.2f}".format(br_currentTempF)) + " Status: "+ br_status + " At current status for: " +str(br_StateTime) )
            print("Living Room : \t Target Temp: "+ ("{:.2f}".format(lr_targetTempF)) + " Current Temp: "+ ("{:.2f}".format(lr_currentTempF)) + " Status: "+ lr_status + " At current status for: " +str(lr_StateTime))
            
            ##check for over limits. Can do additional alerting here. 
            if br_statusNow =="OFF" and br_StateTime>max_current_state_off:
                print ("!!! Bedroom has been OFF for more than " + str(max_current_state_off) + " !!!")
                print("")
            if br_statusNow=="HEATING" and br_StateTime> max_current_state_on:
                print ("!!! Bedroom has been HEATING for more than " +str(max_current_state_off) + "  !!!")
                print("")
            if lr_statusNow =="OFF" and lr_StateTime> max_current_state_off:
                print ("!!! Living Room has been OFF for more than " +str(max_current_state_off) + "  !!!")
                print("")
            if lr_statusNow=="HEATING" and lr_StateTime> max_current_state_on:
                print ("!!! Living Room has been HEATING for more than " +str(max_current_state_off) + "  !!!")
                print("")
except Exception as e:
    print(e)