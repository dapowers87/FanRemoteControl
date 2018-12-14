import time
import datetime
from fan_package.fan_gpio_controller import *
from fan_package.fan import *
from fan_package.fan_enums import *
from fan_package.mqtt_controller import *

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
    
    def print_message(message):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("{}: topic: '{}', payload: '{}'".format(now, message.topic, message.payload))
        
    def toggle_fan_state(fan):
        if fan.fanSpeedState == FanSpeedState.OFF:
            fan.fan_speed_state = FanSpeedState.ON
        else:
            fan.fan_speed_state = FanSpeedState.OFF   
            
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
        toggle_light(True)
    elif message.topic == "fanControl/BedroomFan/light/set":
        print_message(message)
        toggle_light(False)
            
    #Fan On/Off messages
    elif message.topic == "fanControl/OfficeFan/fan/on/set":
        print_message(message)
        
        if office_fan.fan_speed_state == FanSpeedState.ON:
            turn_off_fan(True)
            office_fan.fan_speed_state = FanSpeedState.OFF
        else:
            set_fan_speed(office_fan.fan_speed, True)
            office_fan.fan_speed_state = FanSpeedState.ON
        toggle_fan_state(office_fan)        
    elif message.topic == "fanControl/BedroomFan/fan/on/set":
        print_message(message)
        
        if bedroom_fan.fan_speed_state == FanSpeedState.ON:
            turn_off_fan(False)
            bedroom_fan.fan_speed_state = FanSpeedState.OFF
        else:
            set_fan_speed(bedroom_fan.fan_speed, False)
            bedroom_fan.fan_speed_state = FanSpeedState.ON
        toggle_fan_state(bedroom_fan) 

    #Fan Speed messages
    elif message.topic == "fanControl/OfficeFan/fan/speed/set":
        print_message(message)
        speed = get_fan_speed_enum(message.payload)
        set_fan_speed(speed, True)
        office_fan.fan_speed = speed
        office_fan.fan_speed_state = FanSpeedState.ON
    elif message.topic == "fanControl/BedroomFan/fan/speed/set":
        print_message(message)
        speed = get_fan_speed_enum(message.payload)
        set_fan_speed(speed, False)
        bedroom_fan.fan_speed = speed
        bedroom_fan.fan_speed_state = FanSpeedState.ON

def publish_fan_state():
    m_client.publish("fanControl/OfficeFan/fan/on/state", office_fan.fan_speed_state.name)
    m_client.publish("fanControl/BedroomFan/fan/on/state", bedroom_fan.fan_speed_state.name)
    
    m_client.publish("fanControl/OfficeFan/fan/speed/state", office_fan.fan_speed.name.lower())
    m_client.publish("fanControl/BedroomFan/fan/speed/state", bedroom_fan.fan_speed.name.lower())

try:
    initialize_pins()
    
    office_fan = Fan()
    bedroom_fan = Fan()

    m_client = MqttController(message_parser)
    m_client.connect_to_mqtt()
    while True:
        if not m_client.connected:
            m_client.reconnect_to_mqtt()            
        
        publish_fan_state()        
        
        time.sleep(1)
                
finally:
    cleanup_gpio()
