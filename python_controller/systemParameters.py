import serial
class ThisSystem:
    #
    # This script contains user user-defined parameters contained in the main
    # controller.py file
    ##
    # Logging web service using SQL lite db - can use for testing purposes
    log_url    = "http://localhost:7777/log"
    log_server = "localhost"
    
    ## Logging web service using corporate db
    #log_server = "myserver.com"
    #log_url    = "http://myserverUrl"

    log_filename = 'BarcodeErrors.log'
 
    # BlinkStick info below that proably will not change but should be
    # confirmed via the lsusb terminal command
    idVendor  = 0x20a0
    idProduct = 0x41e5

    # serial port settings below
    #
    serialPort     = '/dev/ttyACM0'
    serialBaudrate = 9600
    serialParity   = serial.PARITY_NONE
    serialStopbits = serial.STOPBITS_ONE
    serialTimeout  = 0.5
    serialXonxoff  = False
    serialRtscts   = False
    serialDsrdtr   = False
    #
    # end serial port settings

    successSound = 'snd/LASER.WAV'
    failSound    = 'snd/BUZZ.WAV'
    instrumentID = 'LVL_H2610_V10_02_10211'
    emailServer  = 'myMailhost.com'
    emailUsers   = 'myEmailAddress@myDomain.com'
    sendEmail    = False
    
