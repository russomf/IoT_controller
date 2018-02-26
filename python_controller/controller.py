# -*- coding: utf-8 -*-
"""
controller.py
"""
import sys
import time
import json
import pygame
import requests
import serial
import os
import stat
import socket
import smtplib
import logging

from email.mime.text import MIMEText
from blinkstick import blinkstick
from requests.exceptions import ConnectionError
from serial.serialutil import SerialException
from logging.handlers import RotatingFileHandler
from datetime import datetime
from systemParameters import ThisSystem
from usb.core import find as finddev
from usb import util

print ("serial.__version__" + serial.VERSION)

# Flags and counters
sp = None
previousPingServerMessage = None
scannerFailedCounter = 0
skipBlinkStick = False
startupCompleted = False

# Set up logging
logger = logging.getLogger("Controller Rotating Log")
logger.setLevel(logging.DEBUG)
handler1 = RotatingFileHandler(ThisSystem.log_filename, maxBytes=100000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler1.setFormatter(formatter)
handler2 = logging.StreamHandler(sys.stdout)
logger.addHandler(handler1)
logger.addHandler(handler2)

# Preload sound files
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.init()
ping = pygame.mixer.Sound(ThisSystem.successSound)
buzz = pygame.mixer.Sound(ThisSystem.failSound)

# Blink one at a time until all are blue
# Must have a mimimum delay of 0.02 seconds when changing colors
def startup(delay=0.15):
    global startupCompleted

    ping.play()
    bs = blinkstick.find_first()
       
    if bs is None:
        startupCompleted = True
        #raise BlinkStickNotConnected
        return False
      
    for i in range(8):
        bs.set_color(channel=0, index=i, name="blue")
        time.sleep(delay)

    startupCompleted = True
        
# Blink change one at a time to green and then back to blue
def success(delay=0.1, hold=0.1):
    ping.play()
    
    if skipBlinkStick == True:
        if isBlinkStickAttached()==True:
            if resetBlinkStick() !=True:
               return
            else:
               logger.info("BlinkStick has been re-attached.")
        else:
            return
    
    bs = blinkstick.find_first()
    if bs is None:
        return False

    for i in range(8):
        bs.set_color(channel=0, index=i, name="green")
        time.sleep(delay)
    time.sleep(hold)

    for i in range(8):
        bs.set_color(channel=0, index=i, name="blue")
        time.sleep(delay)

# Turn all red and stay red
def fail(delay=0.1):

    buzz.play()
   
    if skipBlinkStick:
        if isBlinkStickAttached():
            if resetBlinkStick() is False:
               return
        else:
            return
    
    bs = blinkstick.find_first()
  
    if bs is None:
        return False
   
    for i in range(8):
        bs.set_color(channel=0, index=i, name="red")
        time.sleep(delay)
 
# Turn off all LEDs
def off():
    if skipBlinkStick:
        if isBlinkStickAttached():
            if resetBlinkStick() is False:
               return
        else:
            return
   
    bs = blinkstick.find_first()
    
    if bs is None:
        return False
    
    for i in range(8):
        bs.set_color(channel=0, index=i, name=None)

# Blink Only first LED
def pingSuccess(hold=0.50):
    global skipBlinkStick

    if skipBlinkStick:
        if isBlinkStickAttached():
            if resetBlinkStick() is False:
               return
        else:
            return
    skipBlinkStick = False
    bs = blinkstick.find_first()
      
    if bs is None:
        return False
       
    bs.set_color(channel=0, index=0, name=None)
    time.sleep(hold)
    bs.set_color(channel=0, index=0, name="blue")
    time.sleep(hold)
 
# Log a barcode
def log(barcode, instrument):

    starttime= datetime.utcnow()
    data  = {'BARCODE':barcode, 'INSTRUMENT_NAME':ThisSystem.instrumentID,'START_TIME':starttime}
    resp  = requests.post(ThisSystem.log_url, data=data)
    rdata = json.loads( resp.text )
     
    if rdata['ID']:
        success()
        return rdata['ID']
    else:
        fail()

# Check to see if server is up and running
def pingServer(serverToPing):
    global previousPingServerMessage
  
    # redirect the response of error and messages to a file   
    response = os.system("ping -c 1 " + serverToPing  + "> nodisplay.txt 2>&1")
    time.sleep (0.1)
    if response == 0:
        
        response = "Server " + serverToPing + " is active."
        
        if previousPingServerMessage == response:
            return True
        previousPingServerMessage = response
  
        return True
    else:
        
        response = "Server " + serverToPing + " is DOWN."
       
        if previousPingServerMessage is None:
            print ("response : " + response)
            previousPingServerMessage = response

        return False

# Read the bar code via the serial port
def readBarcode():
    global sp
    global ThisSystem
    global scannerFailedCounter
    
    numTries = 5 # was 20 * 10 second for warmup or 2 minutes
    if scannerFailedCounter > 0:
        logger.info("Cannot find serial port " + ThisSystem.serialPort + " try # : " + str(scannerFailedCounter))
    if scannerFailedCounter >= numTries:
        errMessage = "Rebooting system to resetting serial port to " + ThisSystem.serialPort + " after " + str(numTries) + " tries."
        logger.info(errMessage)
        sendEmail(errMessage)
        os.system('sudo shutdown -r now')
    if scannerFailedCounter > 0:
        logger.info("Cannot find serial port " + ThisSystem.serialPort + " try # : " + str(scannerFailedCounter))
    if not device_exists(ThisSystem.serialPort):
        return None

    # Clear the buffer
    if sp == None:
        sp = serial.Serial(
                port     = ThisSystem.serialPort,
                baudrate = ThisSystem.serialBaudrate,
                parity   = ThisSystem.serialParity,
                stopbits = ThisSystem.serialStopbits,
                timeout  = ThisSystem.serialTimeout,
                xonxoff  = ThisSystem.serialXonxoff,
                rtscts   = ThisSystem.serialRtscts,
                dsrdtr   = ThisSystem.serialDsrdtr
        )
        
    barcode = sp.readline()

    # Convert from btye to string data and remove the carriage return that was generated by the bar code reader
    barcode = str(barcode,'utf-8').rstrip('\r')
    scannerFailedCounter = 0
    return barcode

# Send an email with an error message
def sendEmail(errmsg):
    global lastError, previousError
    
    try:
        if ThisSystem.sendEmail == True:
            ## **************************************************************************
            ## for sending emails when no authentication is required
            ##   
            computerName = socket.gethostname()
            msg = MIMEText(errmsg)
            sendFrom = ThisSystem.instrumentID
            msg['Subject'] = "Error message from " + sendFrom + ". computer : " + computerName
            msg['From'] = ThisSystem.instrumentID
            msg['To'] = ThisSystem.emailUsers
            toRecipients = ThisSystem.emailUsers.split(',') 
            print ("Sending email to : " + ThisSystem.emailUsers)
            print ("Message sent : " + errmsg)
            server = smtplib.SMTP(ThisSystem.emailServer, 25)
            server.starttls()
            server.sendmail(sendFrom, toRecipients, str(msg))
            server.quit()
       
            ## **************************************************************************
            ## for sending emails requing authentication
            ##
            ##computerName = socket.gethostname()
            ##msg = MIMEText(errmsg)
            ##sendFrom = ThisSystem.instrumentID
            ##msg['Subject'] = "Error message from " + sendFrom + ". computer : " + computerName
            ##msg['From'] = ThisSystem.instrumentID
            ##msg['To'] = ThisSystem.emailUsers
            ##toRecipients = ThisSystem.emailUsers.split(',') 
            #print ("Sending the following email msg to : " + + ThisSystem.emailUsers)
            #print ("Message sent : " + errmsg)
            ##server = smtplib.SMTP('smtp.gmail.com', 587)
            ##server.login("williamneil777@gmail.com", "putpasswordinhere")
            ##server.sendmail("FromUser@gmail.com", "WilliamNeil777@gmail.com", str(msg))
            ##server.quit()
            ## **************************************************************************
        else:
            print ("skipping email")
            return
    except Exception as e:
            return

# Determine if the device name exists              
def device_exists(path):
    global scannerFailedCounter
    try:
        if stat.S_ISBLK(os.stat(path).st_mode) == False:
             sp = None
             return True
             
        else:            
            sp = None
            scannerFailedCounter = scannerFailedCounter + 1
            return False
       
    except Exception as e:
        scannerFailedCounter = scannerFailedCounter + 1
        time.sleep(10)
        return False

# Determine the vendor id and product Id by running the lsusb command in terminal
def isBlinkStickAttached():
    try:
        dev = finddev(idVendor = ThisSystem.idVendor, idProduct = ThisSystem.idProduct)
        if dev is not None:
            #manufacturer       = util.get_string(dev,256,1)
            #deviceDescription  = util.get_string(dev,256,2)
            #deviceSerialNumber = util.get_string(dev,256,3)
            #print ("Manufacturer  : " + manufacturer)
            #print ("Device Description  : " + deviceDescription )
            #print ("Device SerialNumber  : " + deviceSerialNumber )
            startup()
            logger.info("BlinkStick is attached")
            return True
        else:
            logger.info("BlinkStick is NOT attached.")        
            return False
    except Exception as e:
        return False

# This will refresh the usb port for the Blink stick after it fails to initialize
# (Without this command it is not possible to call blinkstick.find_first()
# (a second time (an un recoverable exception error unless it is plugged back in and is reset)
def resetBlinkStick():
    return
    print ("resetting BlinkStick")
    dev = finddev(idVendor = 0x20a0, idProduct = 0x41e5)
    if dev is not None:
        logger.info("Resetting usb port after Blink Stick has been attached.")
        dev.reset()
        return True
    else:
         return False

# Run the controller
def runController():
    global skipBlinkStick, startupCompleted, sp
    lastError = None
    previousError = None
    startupCompleted = False
    skipBlinkStick = False
    logger.info("Controller Started.")
            
    while True:
        try:
            if startupCompleted == False:
                logger.info("Initializing BlinkStick.")
                startup()
                  
            barcode = readBarcode()
            if pingServer(ThisSystem.log_server) == True:
                pingSuccess()
            else:
                raise ConnectionError

            if barcode is None:
                time.sleep (0.1)
                continue
                                          
            if len(barcode) > 0:   
                ID = log(barcode,ThisSystem.instrumentID)
                logger.info("Barcode : " + barcode +  " ID returned from server : " + str(ID))   
                previousError = None
                skipBlinkStick = False

        except blinkstick.BlinkStickException as e:
            lastError = e

            if str(lastError) != str(previousError):
                lastErrorMsg = "Blink Stick Exception. Url : " + ThisSystem.log_server
                logger.info(lastError)
                skipBlinkStick = True
                resetBlinkStick()
                fail()
                logger.error(lastError)
                previousError=lastError

        except AttributeError as e:

            print ("Attribute Error")
            if str(lastError) != str(previousError):
                lastErrorMsg = "Blink Stick Attubute Exception. Url : " + ThisSystem.log_server
                logger.info(lastError)
                skipBlinkStick = True
                fail()
                logger.error(lastError)
                previousError=lastError
                resetBlinkStick()

        except USBError as e:
            lastError = e
            
            if str(lastError) != str(previousError):
                lastErrorMsg = "Blink Stick Exception. Url : " + ThisSystem.log_server
                logger.info(lastError)
                skipBlinkStick = True
                fail()
                logger.error(lastError)
                previousError=lastError   
                
        except ConnectionError as e:
             lastError = e
             if str(lastError) != str(previousError):
                   
                previousError = lastError
                lastErrorMsg = str(lastError) + "server : " + ThisSystem.log_url
                fail()
                logger.error(lastErrorMsg)
                               
                          
        except NoSuchSerialPort as e:
            lastError = e
            sp = None
            
            if str(lastError) != str(previousError):
                 
                previousError = lastError
                lastErrorMsg = "Cannot find serial port device: " + ThisSystem.serialPort + ". Barcode reader may not be attached or the port name is incorrect."
                fail()
                logger.error(lastErrorMsg)
                sendEmail(str(lastErrorMsg))
                # give time for scanner to initialize
                time.sleep(10)
                            
        except SerialException as e:
            lastError = e
            sp = None 
            if str(lastError) != str(previousError):
                previousError = lastError
                lastErrorMsg = "Serial Port error: " + ThisSystem.serialPort + ". Barcode reader may not be attached or there is some other error."
                fail()
                logger.error(lastError)
                sendEmail(str(lastErrorMsg))
                previousError=lastError

        except PingServerError as e:
            lastError = e

            if str(lastError) != str(previousError):
                lastErrorMsg = "Ping server error. Url : " + ThisSystem.log_server
                logger.info(lastError)
                fail()
                logger.error(lastError)
                previousError=lastError

        except BrokenPipeError as e:
            lastError = e
            print ("broken pipe caught")
            print (lastError)
            if str(lastError) != str(previousError):
                lastErrorMsg = "BrokenPipeError. Url : " + ThisSystem.log_server
                logger.info(lastError)
                fail()
                logger.error(lastError)
                previousError=lastError
                resetBlinkStick()

        except Exception as e:
            lastError = e
            typeError = type(e).__name__
            if "USBERR" not in typeError:
                
                print ("Unanticipated exception")
                print (type(e).__name__)
                print (e.__class__.__name__)
                print (lastError)
            skipBlinkStick = True
            #resetBlinkStick()
            if str(lastError) != str(previousError):
                   
                previousError = lastError
                lastErrorMsg = "Exception error : " + str(lastError)
                fail()
                logger.error(lastError)
                sendEmail(str(lastErrorMsg))
                previousError=lastError

# Custom Exceptions
class Error(Exception):
    """Base class for other exceptions"""
    pass

##class BlinkStickException(Error):
##    """Raised when the Blinkstick cannot be initialized"""
##    pass

class USBError(Error):
    """Raised when the Blinkstick cannot be initialized"""
    pass

class NoSuchSerialPort(Error):
    """Raised when the serial port does not exist"""
    pass

class PingServerError(Error):
    """Raised when the Blinkstick cannot be initialized"""
    pass

if __name__ == '__main__':
    runController()
