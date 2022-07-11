""" MQTT Camera and IoT Demo Case
    This script provides a ngrok SSH service tunnel to a Raspberry Pi
    Also the local MQTT Settings will be updated and pushed to all Meraki Cameras in a network
"""
import socket
from pyngrok import ngrok
import requests
import json

""" #############   SSH Service Tunnel   ##############
    ### Sebastian Ehrhardt                         ####
    ### mail: sebastian.ehrhardt@telekom.de        ####
    ###                                 11.07.2022 ####
    ################################################### """

""" #### Changes only in this area #### """
ngrok_credentials = "xxxxx"

webex_url = "https://api.ciscospark.com/v1/messages"
webex_access_token = "xxxxx-xx-xx-xx-xxx"
headers = {'Authorization': 'Bearer ' + webex_access_token, 'Content-Type': 'application/json'}
webex_mails = ["Sebastian.Ehrhardt@blabla.de"]
""" ############################################ """

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
