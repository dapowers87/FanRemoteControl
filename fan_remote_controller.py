import time
import datetime
from fan_package import fan_gpio_controller
from fan_package.fan import *
from fan_package.fan_enums import *
from fan_package.mqtt_controller import *
from threading import Thread

def set_fan_state(isOffice, state):
    global office_fan
    global bedroom_fan
    if isOffice:
        office_fan.fan_speed_state = state
    else:
        bedroom_fan.fan_speed_state = state

def message_parser(message):
    #global office_fan
    #global bedroom_fan

    message.payload = message.payload.decode('utf-8')
    
    def print_message(message):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("{}: topic: '{}', payload: '{}'".format(now, message.topic, message.payload))

    def get_fan_speed_enum(message):
        if message.lower() == "low":
            return FanSpeed.LOW
        elif message.lower() == "medium":
            return FanSpeed.MEDIUM
        elif message.lower() == "high":
            return FanSpeed.HIGH

    #Fan Light On/Off messages
    if message.topic == "fanControl/OfficeFan/light/set":
        print_message(message)
        fan_gpio_controller.toggle_light(True)
    elif message.topic == "fanControl/BedroomFan/light/set":
        print_message(message)
        fan_gpio_controller.toggle_light(False)

    #Fan On/Off messages
    elif message.topic == "fanControl/OfficeFan/fan/on/set":
        print_message(message)

        if message.payload == "OFF":
            fan_gpio_controller.turn_off_fan(True)
            office_fan.fan_speed_state = FanSpeedState.OFF
        else:
            fan_gpio_controller.set_fan_speed(office_fan.fan_speed, True)
            office_fan.fan_speed_state = FanSpeedState.ON
    elif message.topic == "fanControl/BedroomFan/fan/on/set":
        print_message(message)

        if message.payload == "OFF":
            fan_gpio_controller.turn_off_fan(False)
            bedroom_fan.fan_speed_state = FanSpeedState.OFF
        else:
            print("test3")
            fan_gpio_controller.set_fan_speed(bedroom_fan.fan_speed, False)
            bedroom_fan.fan_speed_state = FanSpeedState.ON
    #Fan Speed messages
    elif message.topic == "fanControl/OfficeFan/fan/speed/set":
        print_message(message)
        speed = get_fan_speed_enum(message.payload)
        fan_gpio_controller.set_fan_speed(speed, True)
        office_fan.fan_speed = speed
        office_fan.fan_speed_state = FanSpeedState.ON
    elif message.topic == "fanControl/BedroomFan/fan/speed/set":
        print_message(message)
        speed = get_fan_speed_enum(message.payload)
        fan_gpio_controller.set_fan_speed(speed, False)
        bedroom_fan.fan_speed = speed
        bedroom_fan.fan_speed_state = FanSpeedState.ON

def publish_fan_state():
    while True:
        m_client.publish("fanControl/OfficeFan/fan/on/state", office_fan.fan_speed_state.name)
        m_client.publish("fanControl/BedroomFan/fan/on/state", bedroom_fan.fan_speed_state.name)

        m_client.publish("fanControl/OfficeFan/fan/speed/state", office_fan.fan_speed.name.lower())
        m_client.publish("fanControl/BedroomFan/fan/speed/state", bedroom_fan.fan_speed.name.lower())
        
        time.sleep(1)

try:
    office_fan = Fan()
    bedroom_fan = Fan()
    
    fan_gpio_controller.initialize_pins()

    buttonThread = Thread(target = fan_gpio_controller.process_queue)
    buttonThread.daemon = True
    buttonThread.start()

    m_client = MqttController(message_parser)
    m_client.connect_to_mqtt()
    
    publishThread = Thread(target = publish_fan_state)
    publishThread.daemon = True
    publishThread.start()
    
    while True:
        if not m_client.connected:
            m_client.reconnect_to_mqtt()   
        time.sleep(1)
finally:
    fan_gpio_controller.cleanup_gpio()
