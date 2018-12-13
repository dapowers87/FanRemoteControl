import RPi.GPIO as gpio
import time
import paho.mqtt.client as mqtt
from fan_class import *

lightPin = 16
pointPin = 26
lowPin = 25
medPin = 12
highPin = 13
offPin = 6

officeFan = Fan()
bedroomFan = Fan()

Connected = False

pointToOffice = True

gpio.setmode(gpio.BCM)

gpio.setup(lightPin, gpio.OUT)
gpio.setup(pointPin, gpio.OUT)
gpio.setup(lowPin, gpio.OUT)
gpio.setup(medPin, gpio.OUT)
gpio.setup(highPin, gpio.OUT)
gpio.setup(offPin, gpio.OUT)

gpio.output(lightPin, True)
gpio.output(lowPin, True)
gpio.output(medPin, True)
gpio.output(highPin, True)
gpio.output(offPin, True)

def on_connect(client, userdata, flags, rc):
    global Connected                #Use global variable
    Connected = True                #Signal connection

def on_disconnect(client, userdata, flags, rc=0):
    global Connected
    Connected = False

def print_message(message):
    print('\ntopic: {}, payload: "{}"'.format(message.topic, message.payload))

def on_message(client, userdata, message):
    if message.topic == "fanControl/BedroomFan/light/set":
        print_message(message)
        ToggleBedroom()
    elif message.topic == "fanControl/OfficeFan/light/set":
        print_message(message)
        ToggleOffice()

    elif message.topic == "fanControl/OfficeFan/fan/on/set":
        print_message(message)
        set_fan_on_state(message.payload, True, officeFan)
    elif message.topic == "fanControl/BedroomFan/fan/on/set":
        print_message(message)
        set_fan_on_state(message.payload, False, bedroomFan)

    elif message.topic == "fanControl/OfficeFan/fan/speed/set":
        print_message(message)
        set_fan_speed_state(message.payload, True, officeFan)
    elif message.topic == "fanControl/BedroomFan/fan/speed/set":
        print_message(message)
        set_fan_speed_state(message.payload, False, bedroomFan)

def set_fan_on_state(payload, isOffice, fan):
    if isOffice:
        fan = officeFan
        gpio.output(pointPin, True)
    else:
        fan = bedroomFan
        gpio.output(pointPin, False)

    if payload == "OFF":
        fan.fanSpeedState = FanSpeedState.OFF
        TogglePin(offPin)
    elif payload == "ON":
        fan.fanSpeedState = FanSpeedState.ON
        if fan.fanSpeed == FanSpeed.LOW:
            TogglePin(lowPin)
        elif fan.fanSpeed == FanSpeed.MEDIUM:
            TogglePin(medPin)
        elif fan.fanSpeed == FanSpeed.HIGH:
            TogglePin(highPin)

def set_fan_speed_state(payload, isOffice, fan):
    if isOffice == True:
        fan = officeFan
        gpio.output(pointPin, True)
    else:
        fan = bedroomFan
        gpio.output(pointPin, False)
    
    if payload == "low":
        fan.fanSpeed = FanSpeed.LOW
        fan.fanSpeedState = FanSpeedState.ON
        TogglePin(lowPin)
    elif payload == "medium":
        fan.fanSpeed = FanSpeed.MEDIUM
        fan.fanSpeedState = FanSpeedState.ON
        TogglePin(medPin)
    elif payload == "high":
        fan.fanSpeed = FanSpeed.HIGH
        fan.fanSpeedState = FanSpeedState.ON
        TogglePin(highPin)

def connect_to_mqtt():
    global Connected
    global client
    print('Connecting to MQTT')
    Connected = False
    client = mqtt.Client()
    client.username_pw_set("fanPi", "fan")
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    #client.connect("m11.cloudmqtt.com", 11608)
    client.connect("192.168.1.151", 1883)
    client.loop_start()       #connect to broker

    while Connected != True:    #Wait for connection
        time.sleep(0.1)
    print('Connected to MQTT')

    set_subscription()

def reconnect_to_mqtt():
    print("Connection lost to MQTT. Reconnecting...")
    reattemptConnect = True
    global Connected
    while Connected != True:    #Wait for connection
        try:
            if(reattemptConnect == True):
                client.reconnect()

            reattemptConnect = False
        except:
            reattemptConnect = True
            print("reconnect failed")

        time.sleep(1)

        if(Connected == True):
            print("Reconnected... Exiting reconnect loop")
    set_subscription()

def set_subscription():
    client.subscribe("fanControl/#")

def TogglePin(selectedPin):
    gpio.output(selectedPin, False)
    time.sleep(0.5)
    gpio.output(selectedPin, True)

def ToggleBedroom():
    gpio.output(pointPin, False)
    time.sleep(0.5)
    PulseOn()

def ToggleOffice():
    gpio.output(pointPin, True)
    time.sleep(0.5)
    PulseOn()

def PulseOn():
    gpio.output(lightPin, False)
    time.sleep(0.5)
    gpio.output(lightPin, True)

def return_on_state_string(FanSpeedState):
    if FanSpeedState == FanSpeedState.ON:
        return "ON"
    else:
        return "OFF"

def return_speed_state_string(fanSpeed):
    if fanSpeed == FanSpeed.LOW:
        return "low"
    elif fanSpeed == FanSpeed.MEDIUM:
        return "medium"
    else:
        return "high"


try:
    connect_to_mqtt()
    while True:
        if(Connected <> True):
            reconnect_to_mqtt()

        global client
        client.publish("fanControl/OfficeFan/fan/on/state", return_on_state_string(officeFan.fanSpeedState), 0, True)
        client.publish("fanControl/BedroomFan/fan/on/state", return_on_state_string(bedroomFan.fanSpeedState), 0, True)

        client.publish("fanControl/OfficeFan/fan/speed/state", return_speed_state_string(officeFan.fanSpeed), 0, True)
        client.publish("fanControl/BedroomFan/fan/speed/state", return_speed_state_string(bedroomFan.fanSpeed), 0, True)
        time.sleep(1)

        #if pointToOffice:
        #    print("Pointing to Office")
        #else:
        #    print("Pointing to Bedroom")

       # response = int(input('Enter \n\t1 to toggle light\n\t2 to switch target '+
       # '\n\t3 to turn off fan'+
       # '\n\t4 to set fan to low'+
       # '\n\t5 to set fan to med' +
       #'\n\t6 to set fan to high'+
       # '\n\tChoice: '))

        #if response == 1:
         #   PulseOn()
        #elf response == 2:
        #    pointToOffice = not pointToOffice
        #elif response == 3:
        #    TogglePin(offPin)
        #elif response == 4:
        #    TogglePin(lowPin)
        #elif response == 5:
        #    TogglePin(medPin)
        #elif response == 6:
        #    TogglePin(highPin)


        ##if pointToOffice:
         #   gpio.output(pointPin, True)
        #else:
        #    gpio.output(pointPin, False)

finally:
    gpio.cleanup()
