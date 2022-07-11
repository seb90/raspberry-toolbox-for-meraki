# Raspberry Pi Toolbox for Cisco Meraki

The target is to create a device that could map multiple functions. A toolbox for working with Cisco Meraki. To be able to implement these features easily, I have chosen a Raspberry Pi with the Raspbian operating system.</br>
The following functions should be provided:
- [x] Syslog Server
- [x] MQTT Server
- [x] Webhook Server
- [x] SSH Service Tunnel
- [ ] Radius Server
- [ ] DHCP Server
- [ ] SAML SSO Server

The following explains how to install and set up the various functions.</br></br>

***

### 1. Get Raspbian I will not go further into the installation of Raspbian

  ```
  https://www.raspberrypi.com/software/
  ```

**Basic configuration for Raspbian**</br>
First, some basic settings can be made using the configuration tool provided by Raspbian:
  ```
  sudo raspi-config
  ```
After that, we should do some updates:
  ```
  sudo apt-get updates
  sudo apt-get upgrades
  ```

### 2. Install Syslog and display events
The first command installs Syslog, the second command displays all Syslog messages in real time.
  ```
  sudo apt-get install rsyslog
  command tail -f /var/log/syslog
  ```
Now go to your Meraki Organization and configure Syslog:
  > Network-wide -> General -> Reporting
  ```
  Server IP: 'IP from Raspberry'
  Port: 514
  Roles: Air Marshal events, Wireless event log, Switch event log, Security events, Appliance event log
  ```
  
### 3. Install MQTT and display events
  ```
  sudo apt-get install mosquitto mosquitto-clients
  ```
First we allow access to our MQTT and set the port:
  ```
  sudo nano /etc/mosquitto/conf.d/010-listener-with-users.conf
  ```
  > listener 1883</br>
  > allow_anonymous true

Now restart the service and check if it is active:
  ```
  sudo systemctl status mosquitto
  sudo systemctl restart mosquitto
  ```
Now we can listen to different MQTT topics. As wildcard can be used #. To better understand which Topics are available, a brief overview of the current MQTT capabilities at Cisco Meraki.

**Wildcards**</br>
- Plus sign (+): matches any name for a specific topic area ("/merakimv/+/0")
- Hash sign (#): multi level wildcard, can used at the end of the topic ("/merakimv/#")

**Cameras**</br>
How to add an MQTT Broker:
  > Cameras -> Select one -> Settings -> Sense -> MQTT Broker</br>
  ```
  Broker Name: RPi
  Host: 'IP from Raspberry'
  Port: 1883
  ```
Which Topics exist:</br>
- Object detections from whole camera frame:
  > /merakimv/Q2xx-xxxx-xxxx/raw_detections
- Current state of zone:
  > /merakimv/Q2xx-xxxx-xxxx/000000000000
- Audio detections from the camera’s microphone:
  > /merakimv/Q2xx-xxxx-xxxx/audio_detections
- Measurements from the camera’s microphone (dB):
  > /merakimv/Q2xx-xxxx-xxxx/audio_analytics
  
**Environmental (IoT)**</br>
How to add an MQTT Broker:
  > Environmental -> MQTT Brokers -></br>
  ```
  Name: RPi
  Host: 'IP from Raspberry'
  Port: 1883
  ```
Which Topics exist:</br>
- Temperature, Humidity, Door, Water and Button data from an MT:
  > meraki/v1/mt/Network_Id/ble/{deviceMac}/temperature</br>
  > meraki/v1/mt/Network_Id/ble/{deviceMac}/humidity</br>
  > meraki/v1/mt/Network_Id/ble/{deviceMac}/door</br>
  > meraki/v1/mt/Network_Id/ble/{deviceMac}/waterDetection</br>
  > meraki/v1/mt/Network_Id/ble/{deviceMac}/buttonPressed
- Cable and USB Power connected to an MT:
  > meraki/v1/mt/Network_Id/ble/{deviceMac}/cableConnected</br>
  > meraki/v1/mt/Network_Id/ble/{deviceMac}/tamperDetection
- Battery percentage and USB power status:
  > meraki/v1/mt/Network_Id/ble/{deviceMac}/usbPowered</br>
  > meraki/v1/mt/Network_Id/ble/{deviceMac}/batteryPercentage
- RSSI data for an MT:
  > meraki/v1/mt/Network_Id/ble/{deviceMac}/gateway/{gatewayMac}/rssi

**Getting MQTT data**</br>
As we can see from the two topics, this one differs. We have the possibility to listen to only one topic at a time, but we also have the possibility to listen to several topics. With the wildcard we can listen to all subordinate topics.
  ```
  mosquitto_sub -h 127.0.0.1 -v -t meraki/#
  mosquitto_sub -h 127.0.0.1 -v -t /merakimv/#
  mosquitto_sub -h 127.0.0.1 -v -t meraki/# -t /merakimv/#
  mosquitto_sub -h 127.0.0.1 -v -t /merakimv/Q2xx-xxxx-xxxx/audio_analytics
  ```
The -t option allows us to specify a topic and the -v option shows us the entire topic path live.

What good is collecting MQTT data if we don't use it? Nothing!</br>
So let's query the data with a Python script and use it.

First we need a Python Library for MQTT
  ```
  pip install paho-mqtt
  ```
Now lets write a small script, which print all MQTT messages:
  ```
  import paho.mqtt.client as mqtt

  def on_message(client, userdata, message):
     print("message received ", str(message.payload.decode("utf-8")))
     print("message topic=", message.topic)


  mqttBroker = "127.0.0.1"  # ip of the server
  client = mqtt.Client('my-mqtt-client')  # create instance
  client.connect(mqttBroker)  # connect to broker
  client.subscribe("meraki/v1/mt/#")  # subscribe to topic

  client.on_message = on_message  # call function for messages
  client.loop_forever()  # start an endless loop
  ```
  
  So we get all the messages and topics, to make sense of the data we have to look inside the data. (See file: mqtt_subscribe.py)
  ```
  import paho.mqtt.client as mqtt
  import json

  def on_message(client, userdata, message):
     data = json.loads(message.payload.decode("utf-8"))
     if 'action' in data:
        if data['action'] == 'shortPress':
           print('Short Press - do something')
        if data['action'] == 'longPress':
           print('Long Press - do something')
     if 'open' in data:
        if data['open'] is True:
           print('Door is open - do something')


  mqttBroker = "127.0.0.1"  # ip of the server
  client = mqtt.Client('my-mqtt-client')  # create instance
  client.connect(mqttBroker)  # connect to broker
  client.subscribe("meraki/v1/mt/#")  # subscribe to topic

  client.on_message = on_message  # call function for messages
  client.loop_forever()  # start an endless loop
  ```
  
### 4. Install a Webhook Server
A webhook is in "principle" the opposite direction to the API. So we need a server that reacts to incoming messages or executes actions.
First we need a Python Library for a Webserver
  ```
  pip install flask
  ```
Now lets write a small script, which print all incoming Webhook messages:
  ```
  from flask import Flask, request, Response

  app = Flask(__name__)  # create instance


  @app.route('/webhook', methods=['POST'])  # define endpoint
  def respond():
     """ if a webhook is incoming, return status code 200 and print the json """
     if request.method == 'POST':  # if POST
        print(request.json)  # print webhook (json input)
        return Response(status=200)  # return status code 200


  if __name__ == '__main__':
     app.run(host='0.0.0.0', debug=True, port=19000)
  ```
Problem: Meraki webhooks are coming from Meraki Cloud. Accordingly, we need access from external.
We now have two options. Either we open a port, which we forward to the Raspberry. Alternatively we can use ngrok to establish a connection from external.

**How to use ngrok?**</br>
First download and install ngrok:
  > https://ngrok.com/download

After this just run it for a specific port:
  ```
  ngrok http 19000
  ```

**How to use ngrok?**</br>
In order to be able to receive webhooks from Meraki, they still have to be configured:
  > Network-wide -> Alerts -> Webhooks</br>
  ```
  Name: Raspberry Pi
  URL: https://00aa-00-00-000-00.ngrok.io/webhook
  Shared secret: 'your secret'
  ```
Now you should get a webhook by clicking on "send test webhook".

### 5. Automatic SSH Service Tunnel
If a Raspberry is to be used remotely, it is often useful to build a service tunnel to have access to the system at any time. To increase the comfort, the script should send the tunnel url to us via Webex.
The first thing we need is pyngrok for our script. 
  ```
  pip install pyngrok
  ```
Now we can create a new python script
  ```
  from pyngrok import ngrok
  import requests
  import json
  
  ngrok_credentials = "xxxx"
  webex_url = "https://api.ciscospark.com/v1/messages"
  webex_access_token = "xxxx-xxx-xxx-xx-xxx"
  headers = {'Authorization': 'Bearer ' + webex_access_token, 'Content-Type': 'application/json'}
  webex_mails = ["Sebastian.Ehrhardt@blabla.de"]
  
  # Initiate ngrok SSH Tunnel
  ngrok.set_auth_token(ngrok_credentials)
  ssh_tunnel = ngrok.connect(22, "tcp")
  tunnel = str(ngrok.get_tunnels())[22:].split('" -> "')[0]
  
  # Send all Information to Webex
  message = f'*Raspberry Pi - DevNet Demo*\n System is now online\n SSH Service Tunnel is successfully started on {tunnel}'
  for mail in webex_mails:
    payload = json.dumps({"toPersonEmail": mail, "markdown": message, "text": message})
    response = requests.request("POST", webex_url, headers=headers, data=payload)

  while True:  # to keep the ngrok tunnel up
    do_nothing = 1
  ```

### 6. Install Radius with Gui
I decided to use FreeRADIUS in the backend and daloRADIUS in the frontend.
  > https://bytexd.com/freeradius-debian/