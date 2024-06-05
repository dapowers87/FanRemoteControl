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
            toggle_fan_light_state(office_fan, True)            
    elif message.topic == "fanControl/BedroomFan/light/set":
        print_message(message)
        
        if message.payload == "ON" and bedroom_fan.fan_light == FanLight.OFF or message.payload == "OFF" and bedroom_fan.fan_light == FanLight.ON: 
            fan_gpio_controller.toggle_light(False)
            toggle_fan_light_state(bedroom_fan, False)

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
        toggle_fan_light_state(bedroom_fan, False)
    elif message.topic == "fanControl/FlipOffice":
        print_message(message)
        toggle_fan_light_state(office_fan, True)
        
def get_fan_speed_number(fan_speed):
        if fan_speed == FanSpeed.LOW:
            return 1
        elif fan_speed == FanSpeed.MEDIUM:
            return 2
        elif fan_speed == FanSpeed.HIGH:
            return 3
        
def persist_state():
    while True:
        write_boolean_to_file(office_fan.fan_light == FanLight.ON, "/home/david/fan_states/office_state")
        write_boolean_to_file(bedroom_fan.fan_light == FanLight.ON, "/home/david/fan_states/bedroom_state") 
        time.sleep(1)

def publish_fan_state():
    while True:
        m_client.publish("fanControl/OfficeFan/fan/on/state", office_fan.fan_speed_state.name)
        m_client.publish("fanControl/BedroomFan/fan/on/state", bedroom_fan.fan_speed_state.name)

        m_client.publish("fanControl/OfficeFan/fan/speed/state", get_fan_speed_number(office_fan.fan_speed))
        m_client.publish("fanControl/BedroomFan/fan/speed/state", get_fan_speed_number(bedroom_fan.fan_speed))
        
        m_client.publish("fanControl/OfficeFan/fan/light/state", office_fan.fan_light.name)
        m_client.publish("fanControl/BedroomFan/fan/light/state", bedroom_fan.fan_light.name)        
        time.sleep(1)

def write_boolean_to_file(boolean_value, filename):
  """Writes a boolean value to a file as a string.

  Args:
    boolean_value: The boolean value to be written.
    filename: The name of the file to write to.
  """
  with open(filename, 'w') as file:
    file.write(str(boolean_value))

def toggle_fan_light_state(fan, is_office):
    if fan.fan_light == FanLight.ON:
        fan.fan_light = FanLight.OFF
    else:
        fan.fan_light = FanLight.ON
     
def office_fan_light_state_override(channel):
    toggle_fan_light_state(office_fan, True)

def bedroom_fan_light_state_override(channel):
    toggle_fan_light_state(bedroom_fan, False)

def read_boolean_from_file(filename):
  """Reads a boolean value from a file that contains a string representation.

  Args:
    filename: The name of the file to read from.

  Returns:
    The boolean value read from the file, or None if the file is empty or the value is invalid.
  """
  try:
    with open(filename, 'r') as file:
      data = file.read().strip()  # Read and remove leading/trailing whitespace
      if data:  # Check if there's any data in the file
        return data.lower() == 'true'  # Convert to lowercase and compare
      else:
        return None  # Handle empty file
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return None
  
try:
    office_fan = Fan()
    if read_boolean_from_file("/home/david/fan_states/office_state"):
        office_fan.fan_light = FanLight.ON
    else: 
        office_fan.fan_light = FanLight.OFF

    bedroom_fan = Fan()
    if read_boolean_from_file("/home/david/fan_states/bedroom_state"):
        bedroom_fan.fan_light = FanLight.ON
    else: 
        bedroom_fan.fan_light = FanLight.OFF
    
    fan_gpio_controller.bedroom_fan_function = bedroom_fan_light_state_override
    fan_gpio_controller.office_fan_function = office_fan_light_state_override
    
    fan_gpio_controller.initialize_pins()

    persistThread = Thread(target = persist_state)
    persistThread.daemon = True
    persistThread.start()
    
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
