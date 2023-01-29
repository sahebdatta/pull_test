from paho.mqtt import client as mqtt_client
import uuid
import time
import threading
import json
import os
import core_temp
# import psutil

mqtt_broker = "192.168.20.254"
mqtt_port = 1883

device_id = 123456789
product_id = 9876543210
system_type = "arm"
os_name = "Linux"
timezone = "UTC+05:30"

user_id = 5

global start_heartbeat, heartbeat_time

prev_time_doing_things = prev_time_doing_nothing = 0

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client()
    client.on_connect = on_connect
    client.connect(mqtt_broker, mqtt_port)
    return client

def mqtt_pub(topic, msg):
    global client
    result = client.publish(topic, msg)
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        status()

    client.subscribe("status")
    client.on_message = on_message

def client_loop(client):
    client.loop_forever()

def status():
    global start_heartbeat, heartbeat_time
    start_heartbeat = True
    heartbeat_time = time.time()

def connect_init(user_ID, device_id):
    global start_heartbeat, heartbeat_time
    system_info = get_system_info()
    system_info["user_id"] = user_ID
    system_info["time_registered"] = str(time.time()).replace(".", "")
    system_info["device_id"] = str(device_id)
    system_info["status"] = "active"
    system_info["heartbeat"] = system_info["time_registered"]
    system_info["services"] = [{}]
    mqtt_pub("connect_init", json.dumps(system_info))
    start_heartbeat = True

    start_heartbeat, heartbeat_time = start_heartbeat, time.time()

def get_system_info():
    output = {}   
    # arrange the string into clear info
    output["product_id"] = product_id
    output["system_type"] = system_type
    output["os_name"] = os_name
    output["timezone"] = timezone
    output["mac_id"] = str(hex(uuid.getnode()))[2:]
    
    return output

def cpu_percent():
    global prev_time_doing_things, prev_time_doing_nothing
    with open("/proc/stat") as procfile:
        cpustats = procfile.readline().split()

    if cpustats[0] != 'cpu':
        raise ValueError("First line of /proc/stat not recognised")

    time_doing_things = int(cpustats[1]) + int(cpustats[2]) + int(cpustats[3])
    time_doing_nothing = int(cpustats[4]) + int(cpustats[5])
    
    diff_time_doing_things = time_doing_things - prev_time_doing_things
    diff_time_doing_nothing = time_doing_nothing - prev_time_doing_nothing
    cpu_percentage = 100.0 * diff_time_doing_things/ (diff_time_doing_things + diff_time_doing_nothing)

    prev_time_doing_things = time_doing_things
    prev_time_doing_nothing = time_doing_nothing

    return cpu_percentage

# def core_temp():
#     with open("/sys/class/hwmon/hwmon*/temp*_*") as procfile:
#         cpustats = procfile.readline().split()
#     print (cpustats)
    

def heartbeat(user_ID, device_id):
    json_str = {}
    json_str["user_id"] = user_ID
    json_str["device_id"] = device_id
    json_str["heartbeat"] = int(time.time())
    json_str["cpu"] = int(cpu_percent())
    tot_m, used_m, free_m = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
    json_str["memory"] = int(used_m*100/tot_m)
    json_str["temperature"] = int(core_temp.sensors_temperatures())
    # try:
    #     json_str["temperature"] = int(psutil.sensors_temperatures()['cpu_thermal'][0][1])
    # except:
    #     json_str["temperature"] = 0

    mqtt_pub(str(user_ID)+"/heartbeat", json.dumps(json_str))

def run(user_ID):
    global start_heartbeat, heartbeat_time, client

    client = connect_mqtt()
    subscribe(client)
    x = threading.Thread(target=client_loop, args=(client,))
    x.start()
    # client.loop_forever()

    connect_init(user_ID, device_id)
    heartbeat_count = 999
    try:
        while True:
            if start_heartbeat:
                heartbeat_count = 0
                start_heartbeat = False
            if heartbeat_count < 12 and (time.time() - heartbeat_time) > 5:
                heartbeat(user_ID, device_id)
                heartbeat_count += 1
                heartbeat_time = time.time()
    
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    # psutil.cpu_percent()
    run(user_id)