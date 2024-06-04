import time
import datetime
from fan_package import fan_gpio_controller
from fan_package.fan import *
from fan_package.fan_enums import *
from fan_package.mqtt_controller import *
from threading import Thread

print("Fan remote controller")

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
        if message == "1":
            return FanSpeed.LOW
        elif message == "2":
            return FanSpeed.MEDIUM
        elif message == "3":
            return FanSpeed.HIGH

    #Fan Light On/Off messages
    if message.topic == "fanControl/OfficeFan/light/set":
        print_message(message)
        
        if message.payload == "ON" and office_fan.fan_light == FanLight.OFF or message.payload == "OFF" and office_fan.fan_light == FanLight.ON: 
            fan_gpio_controller.toggle_light(True)
            toggle_fan_light_state(office_fan)            
    elif message.topic == "fanControl/BedroomFan/light/set":
        print_message(message)
        
        if message.payload == "ON" and bedroom_fan.fan_light == FanLight.OFF or message.payload == "OFF" and bedroom_fan.fan_light == FanLight.ON: 
            fan_gpio_controller.toggle_light(False)
            toggle_fan_light_state(bedroom_fan)

    #Fan On/Off messages
    elif message.topic == "fanControl/OfficeFan/fan/on/set":
        print_message(message)

        if message.payload == "OFF":
            fan_gpio_controller.turn_off_fan(True)
            office_fan.fan_speed_state = FanSpeedState.OFF
        else:
            if office_fan.fan_speed_state == FanSpeedState.OFF:
                fan_gpio_controller.set_fan_speed(office_fan.fan_speed, True)
                office_fan.fan_speed_state = FanSpeedState.ON
    elif message.topic == "fanControl/BedroomFan/fan/on/set":
        print_message(message)

        if message.payload == "OFF":
            fan_gpio_controller.turn_off_fan(False)
            bedroom_fan.fan_speed_state = FanSpeedState.OFF
        else:
            if bedroom_fan.fan_speed_state == FanSpeedState.OFF:
                fan_gpio_controller.set_fan_speed(bedroom_fan.fan_speed, False)
                bedroom_fan.fan_speed_state = FanSpeedState.ON
    #Fan Speed messages
    elif message.topic == "fanControl/OfficeFan/fan/speed/set":
        print_message(message)
        if message.payload == "0":
            fan_gpio_controller.turn_off_fan(True)
            office_fan.fan_speed_state = FanSpeedState.OFF
        else:
            speed = get_fan_speed_enum(message.payload)
            fan_gpio_controller.set_fan_speed(speed, True)
            office_fan.fan_speed = speed
            office_fan.fan_speed_state = FanSpeedState.ON
    elif message.topic == "fanControl/BedroomFan/fan/speed/set":
        print_message(message)
        if message.payload == "0":
            fan_gpio_controller.turn_off_fan(False)
            bedroom_fan.fan_speed_state = FanSpeedState.OFF
        else:
            speed = get_fan_speed_enum(message.payload)
            fan_gpio_controller.set_fan_speed(speed, False)
            bedroom_fan.fan_speed = speed
            bedroom_fan.fan_speed_state = FanSpeedState.ON
    #Fan Light Flip messages
    elif message.topic == "fanControl/FlipBedroom":
        print_message(message)
        toggle_fan_light_state(bedroom_fan)
    elif message.topic == "fanControl/FlipOffice":
        print_message(message)
        toggle_fan_light_state(office_fan)
        
def get_fan_speed_number(fan_speed):
        if fan_speed == FanSpeed.LOW:
            return 1
        elif fan_speed == FanSpeed.MEDIUM:
            return 2
        elif fan_speed == FanSpeed.HIGH:
            return 3

def publish_fan_state():
    while True:
        m_client.publish("fanControl/OfficeFan/fan/on/state", office_fan.fan_speed_state.name)
        m_client.publish("fanControl/BedroomFan/fan/on/state", bedroom_fan.fan_speed_state.name)

        m_client.publish("fanControl/OfficeFan/fan/speed/state", get_fan_speed_number(office_fan.fan_speed))
        m_client.publish("fanControl/BedroomFan/fan/speed/state", get_fan_speed_number(bedroom_fan.fan_speed))
        
        m_client.publish("fanControl/OfficeFan/fan/light/state", office_fan.fan_light.name)
        m_client.publish("fanControl/BedroomFan/fan/light/state", bedroom_fan.fan_light.name)        
        time.sleep(1)

def toggle_fan_light_state(fan):
    if fan.fan_light == FanLight.ON:
        fan.fan_light = FanLight.OFF
    else:
        fan.fan_light = FanLight.ON
    
def office_fan_light_state_override(channel):
    toggle_fan_light_state(office_fan)

def bedroom_fan_light_state_override(channel):
    toggle_fan_light_state(bedroom_fan)

try:
    office_fan = Fan()
    bedroom_fan = Fan()
    
    fan_gpio_controller.bedroom_fan_function = bedroom_fan_light_state_override
    fan_gpio_controller.office_fan_function = office_fan_light_state_override
    
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
