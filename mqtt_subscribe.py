import paho.mqtt.client as mqtt
import json


def on_message(client, userdata, message):
    data = json.loads(message.payload.decode("utf-8"))
    print(data)
    print("message received: ", str(message.payload.decode("utf-8")))
    print("message topic: ", message.topic)
    if 'action' in str(data):
        if data['action'] == 'shortPress':
            print('Short Press')
        if data['action'] == 'longPress':
            print('Long Press')
    if 'open' in str(data):
        if data['open'] is True:
            print('Door is open!')


mqttBroker = "172.24.1.8"  # ip of the server
client = mqtt.Client('my-mqtt-client')  # create instance
client.connect(mqttBroker)  # connect to broker
client.subscribe("meraki/v1/mt/#")  # subscribe to topic
#client.subscribe("/merakimv/#")

client.on_message = on_message  # call function for messages
client.loop_forever()  # start an endless loop
