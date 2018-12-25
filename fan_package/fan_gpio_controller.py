import RPi.GPIO as gpio
from fan_enums import *
import time
import logging 

#Pins currently being used to control the remote

#Pin attached to the light toggle button
LIGHT_TOGGLE_PIN = 16

#Pin attached to the DIP on the remote.
#This tells the remote which fan to signal
DIP_PIN = 26

#Pins attached to the fan speed states
FAN_OFF_PIN = 6
FAN_LOW_PIN = 25
FAN_MED_PIN = 12
FAN_HIGH_PIN = 13

queue = []

def initialize_pins():
    gpio.setmode(gpio.BCM)

    gpio.setup(LIGHT_TOGGLE_PIN, gpio.OUT)
    gpio.setup(DIP_PIN, gpio.OUT)
    gpio.setup(FAN_OFF_PIN, gpio.OUT)
    gpio.setup(FAN_LOW_PIN, gpio.OUT)
    gpio.setup(FAN_MED_PIN, gpio.OUT)
    gpio.setup(FAN_HIGH_PIN, gpio.OUT)

    #Remote is triggered with a low signal, set all high
    gpio.output(LIGHT_TOGGLE_PIN, True)
    gpio.output(DIP_PIN, True)
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
                time.sleep(0.5)
                gpio.output(selected_pin, True)
        except Exception as ex:
            logging.exception(ex)
        time.sleep(0.25)


def set_fan(is_office):
    """ Method used to point the system to a remote
    For is_office, True points to the office fan,
    False points to the bedroom fan
    """
    if is_office:
        gpio.output(DIP_PIN, True)
    else:
        gpio.output(DIP_PIN, False)

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
