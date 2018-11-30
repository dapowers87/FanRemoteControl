import RPi.GPIO as gpio
import time
import paho.mqtt.client as mqtt

lightPin = 16
pointPin = 26
lowPin = 25
medPin = 12
highPin = 13
offPin = 6

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

def on_message(client, userdata, message):
	print('\ntopic: {}, payload: {}'.format(message.topic, message.payload))
	if message.topic == "fanControl/BedroomFan/light/set":
		#print("bedroom light toggle received")
		ToggleBedroom()
	elif message.topic == "fanControl/OfficeFan/light/set":
		#print("office light toggle received")
		ToggleOffice()
	elif message.topic == "fanControl/OfficeFan/fan/set":
		SetFanSpeed(message.payload, True)
	elif message.topic == "fanControl/BedroomFan/fan/set":
		SetFanSpeed(message.payload, False)		
	else:
		print('neither')
    
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

client.subscribe("fanControl/#")

def SetFanSpeed(speed, isOffice):
	if isOffice:
		gpio.output(pointPin, True)
	else:
		gpio.output(pointPin, False)
	
	
	if speed == "off":
		TogglePin(offPin)
	elif speed == "low":
		TogglePin(lowPin)
	elif speed == "medium":
		TogglePin(medPin)
	elif speed == "high":
		TogglePin(highPin)

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

try:
	while True:
		if pointToOffice:
			print("Pointing to Office")
		else:
			print("Pointing to Bedroom")
			
			
		response = int(input('Enter 1 to pulse, 2 to switch target: '))
		
		if response == 1:
			PulseOn()
		elif response == 2:
			pointToOffice = not pointToOffice
		elif response == 3: 
			TogglePin(offPin)
		elif response == 4: 
			TogglePin(lowPin)
		elif response == 5: 
			TogglePin(medPin)
		elif response == 6: 
			TogglePin(highPin)			
			
			
		if pointToOffice:
			gpio.output(pointPin, True)
		else:
			gpio.output(pointPin, False)
			
finally:
	gpio.cleanup()
