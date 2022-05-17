import RPi.GPIO as GPIO
import time
import signal
import sys
import os
import Si7021
import pigpio
from time import sleep

#lcd codes
import drivers

display = drivers.Lcd()

# Configuration
FAN_PIN = 26           # BCM pin used to drive PWM fan
WAIT_TIME = 1           # [s] Time to wait between each refresh
PWM_FREQ = 25          # [kHz] 25kHz for Noctua PWM control

# Configurable temperature and fan speed
MIN_TEMP = 24
MAX_TEMP = 28

FAN_OFF = 0
FAN_LOW = 40
FAN_MEDIUM = 70
FAN_HIGH = 100



FAN_MAX = 100

roomTemp = 0
roomHum = 0

# Get CPU's temperature
def getCpuTemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    cpuTemp =(res.replace("temp=","").replace("'C\n",""))
    print("CPU temp is {0} °C".format(cpuTemp)) # Uncomment for testing
    return cpuTemp

#get temp and humidity from sensors
def getSensorValues():
    #setting up the si7021
    pi = pigpio.pi()
    if not pi.connected:
       exit(0)
    s = Si7021.sensor(pi)
    
    # set the resolution
    # 0 denotes the maxium available: Humidity 12 bits, Temperature 14 bitss
    # See the documentation for more details
    s.set_resolution(0)
    
    roomTemp = s.temperature()
    roomHum = s.humidity()
    s.cancel()
    pi.stop()
    print("Room temp is {0:.3f} °C".format(roomTemp)) # Uncomment for testing
    print("Room Humidity is {0:.3f} rH%".format(roomHum)) # Uncomment for testing
    lcd_text = "Temp:{0:.1f}".format(roomTemp) + " Hum:{0:.1f}".format(roomHum)
    #print(lcd_text)
    display.lcd_display_string(lcd_text, 1)
    sleep(2)
    return roomTemp

# Set fan speed
def setFanSpeed(speed):
    fan.start(speed)
    #print("fan speeed is {0}".format(speed))
    return()


# Handle fan speed
def handleFanSpeed():
    temp = float(getSensorValues())
    cpuTemp = float(getCpuTemperature())
    #temp = cpuTemp #change here
    #temp = 29
    # Turn off the fan if temperature is below MIN_TEMP
    if temp < MIN_TEMP:
        setFanSpeed(FAN_LOW)
        print("Fan LOW") # Uncomment for testing
        display.lcd_display_string("Fan is at LOW", 2)
        
    # Set fan speed to MAXIMUM if the temperature is above MAX_TEMP
    elif temp > MAX_TEMP:
        setFanSpeed(FAN_MAX)
        print("Fan MAX") # Uncomment for testing
        display.lcd_display_string("Fan is at MAX", 2)
        
    # Caculate dynamic fan speed
    else:
        step = (FAN_HIGH - FAN_LOW)/(MAX_TEMP - MIN_TEMP)   
        temp -= MIN_TEMP
        speed = FAN_LOW + (round(temp) * step )
        setFanSpeed(speed)
        print("fan speed .... {0}\n".format(speed))
        display.lcd_display_string("Fan at {0:.0f}%".format(speed), 2)
    return ()

try:
    # Setup GPIO pin
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(FAN_PIN, GPIO.OUT, initial=GPIO.LOW)
    fan = GPIO.PWM(FAN_PIN,PWM_FREQ)
    setFanSpeed(FAN_OFF)
    display.lcd_display_string("DigiPanel", 1)
    sleep(2)
    
    # Handle fan speed every WAIT_TIME sec
    while True:
        handleFanSpeed()
        time.sleep(WAIT_TIME)

except KeyboardInterrupt: # trap a CTRL+C keyboard interrupt
    setFanSpeed(100)
    GPIO.cleanup() # resets all GPIO ports used by this function
    display.lcd_clear() 
    sys.exit()