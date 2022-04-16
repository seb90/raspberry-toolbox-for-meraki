"""
    MQTT script that takes a snapshot when a person is detected on a camera.
    After that the snapshot will be downloaded.
"""
import paho.mqtt.client as mqtt
import json, time, datetime, wget, meraki, requests, include

api = meraki.DashboardAPI(api_key=include.API_KEY, base_url=include.BASE_URL, output_log=False, print_console=False)


def create_snapshot(serial):
    snapshot = api.camera.generateDeviceCameraSnapshot(serial)  # create a snapshot
    snap = requests.get(snapshot['url'], stream=True)  # try to get snapshot
    while snap.status_code != 200:  # snapshot already ready?
        time.sleep(0.1)
        snap = requests.get(snapshot['url'], stream=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # create date for filename
    wget.download(snapshot['url'], out=now+".jpg")  # download snapshot
    return snapshot['url']  # return url


def on_message(client, userdata, message):
    data = json.loads(message.payload.decode("utf-8"))
    if 'counts' in data:
        if data['counts']['person'] > 0:
            result = create_snapshot(include.SERIAL)
            print(message.topic + " " + str(data) + " " + result)
            time.sleep(3)


mqttBroker = "172.24.1.8"  # ip of the server
client = mqtt.Client('my-mqtt-client')  # create instance
client.connect(mqttBroker)  # connect to broker
client.subscribe("/merakimv/" + include.SERIAL + "/662029145223463724")  # subscribe to topic

client.on_message = on_message  # call function for messages
client.loop_forever()  # start an endless loop
