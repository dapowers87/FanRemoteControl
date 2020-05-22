import RPi.GPIO as gpio
from .fan_enums import *
import time
import logging 

office_fan_function = None
bedroom_fan_function = None

#Button press length
BUTTON_PRESS_LEN = 0.4

#Pins currently being used to control the remote

#Pin attached to the light toggle button
LIGHT_TOGGLE_PIN = 16

#Pin attached to the DIP on the remote.
#This tells the remote which fan to signal
OFFICE_DIP_PIN = 23
BEDROOM_DIP_PIN = 26

#Pins attached to the fan speed states
FAN_OFF_PIN = 6
FAN_LOW_PIN = 25
FAN_MED_PIN = 12
FAN_HIGH_PIN = 13

#Input buttons to fix bad light state
BEDROOM_LIGHT_OVERRIDE = 20
OFFICE_LIGHT_OVERRIDE = 21

queue = []

def initialize_pins():
    gpio.setmode(gpio.BCM)

    gpio.setup(LIGHT_TOGGLE_PIN, gpio.OUT)
    gpio.setup(OFFICE_DIP_PIN, gpio.OUT)
    gpio.setup(BEDROOM_DIP_PIN, gpio.OUT)
    gpio.setup(FAN_OFF_PIN, gpio.OUT)
    gpio.setup(FAN_LOW_PIN, gpio.OUT)
    gpio.setup(FAN_MED_PIN, gpio.OUT)
    gpio.setup(FAN_HIGH_PIN, gpio.OUT)
    gpio.setup(BEDROOM_LIGHT_OVERRIDE, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    gpio.setup(OFFICE_LIGHT_OVERRIDE, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    
    gpio.add_event_detect(BEDROOM_LIGHT_OVERRIDE, gpio.RISING, callback=bedroom_fan_function, bouncetime=300)
    gpio.add_event_detect(OFFICE_LIGHT_OVERRIDE, gpio.RISING, callback=office_fan_function, bouncetime=300)

    #Remote is triggered with a low signal, set all high
    gpio.output(LIGHT_TOGGLE_PIN, True)
    gpio.output(OFFICE_DIP_PIN, True)
    gpio.output(BEDROOM_DIP_PIN, True)
    gpio.output(FAN_OFF_PIN, True)
    gpio.output(FAN_LOW_PIN, True)
    gpio.output(FAN_MED_PIN, True)
    gpio.output(FAN_HIGH_PIN, True)    

def queue_button(selected_pin, is_office):
    """ Method used to queue a button press simulation on the remote
    """
    queue.append((selected_pin, is_office))

def process_queue():
    while True:
        try:
            if len(queue) > 0:                
                selected_pin, is_office = queue.pop(0)
                set_fan(is_office)
                
                gpio.output(selected_pin, False)
                time.sleep(BUTTON_PRESS_LEN)
                gpio.output(selected_pin, True)
                
        except Exception as ex:
            logging.exception(ex)
        time.sleep(0.5)


def set_fan(is_office):
    """ Method used to point the system to a remote
    For is_office, True points to the office fan,
    False points to the bedroom fan
    """
    if is_office:
        gpio.output(BEDROOM_DIP_PIN, True)
        gpio.output(OFFICE_DIP_PIN, False)
    else:
        gpio.output(BEDROOM_DIP_PIN, False)
        gpio.output(OFFICE_DIP_PIN, True)
               
    time.sleep(0.25) #Give time to set

def toggle_light(is_office):
    """ Method used to toggle the fan light
    """
    queue_button(LIGHT_TOGGLE_PIN, is_office)

def set_fan_speed(fanSpeed, is_office):
    """ Method used to set the fan speed (low, med, high)
    NOT ON/OFF
    """
    if fanSpeed == FanSpeed.LOW:
        queue_button(FAN_LOW_PIN, is_office)
    elif fanSpeed == FanSpeed.MEDIUM:
        queue_button(FAN_MED_PIN, is_office)
    elif fanSpeed == FanSpeed.HIGH:
        queue_button(FAN_HIGH_PIN, is_office)

def turn_off_fan(is_office):
    """ Method used to set the fan On/Off state
    """
    queue_button(FAN_OFF_PIN, is_office)

def cleanup_gpio():
    gpio.cleanup()
