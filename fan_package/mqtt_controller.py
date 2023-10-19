import paho.mqtt.client as mqtt
import time

class MqttController:
    
    #Class members
    __message_parser = None
    __mqtt_client = None
    connected = False
    
    def __init__(self, message_parser):
        self.__message_parser = message_parser

    def on_connect(self, client, userdata, flags, rc):
        self.connected = True

    def on_disconnect(self, client, userdata, flags, rc=0):
        self.connected = False

    def on_message(self, client, userdata, message):
        self.__message_parser(message)

    def connect_to_mqtt(self):        
        print('Connecting to MQTT')
        self.connected = False
        self.__mqtt_client = mqtt.Client()
        self.__mqtt_client.username_pw_set("fanPi", "F@nP!")
        self.__mqtt_client.on_message = self.on_message
        self.__mqtt_client.on_connect = self.on_connect
        self.__mqtt_client.on_disconnect = self.on_disconnect
        self.__mqtt_client.connect("m93p", 1883)
        self.__mqtt_client.loop_start()       #connect to broker

        while not self.connected:    #Wait for connection
            time.sleep(0.25)
            
        print('Connected to MQTT')

        self.set_subscription()

    def reconnect_to_mqtt(self):
        print("Connection lost to MQTT. Reconnecting...")
                
        timeout = 1
        while not self.connected:    #Wait for connection
            try:
                if reattemptConnect:
                    self.__mqtt_client.reconnect()

                break
            except:
                reattemptConnect = True
                print("reconnect failed")

            time.sleep(timeout)
            
            timeout = timeout * 2
            
            if timeout > 60:
                timeout = 60

            if(self.connected == True):
                print("Reconnected...")
        self.set_subscription()

    def set_subscription(self):
        self.__mqtt_client.subscribe("fanControl/#")
    
    def publish(self, topic, payload):
        self.__mqtt_client.publish(topic, payload, 0, True)
