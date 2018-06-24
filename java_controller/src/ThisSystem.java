/*
 * ThisSystem.java
 * 
 * Author: Mark F. Russo, Ph.D.
 * Copyright (c) 2018 Mark F. Russo, PhD
 * 
 * This is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this software.  If not, see <http://www.gnu.org/licenses/>.
 */

import gnu.io.SerialPort;

public class ThisSystem {
    // Logging web service using SQLlite db - can use for testing purposes
    public static String log_url 		= "http://localhost:7777/log";
    public static String log_server 	= "localhost";
    public static String log_filename 	= "BarcodeErrors.log";
 
    // BlinkStick info below that probably will not change but should be confirmed via the lsusb terminal command
    public static int idVendor 			= 0x20a0;
    public static int idProduct 		= 0x41e5;

    // serial port settings below
    //public static String serialPort = "/dev/ttyACM0";	// Linux
    public static String serialPort 	= "COM3";		// Windows
    public static int serialBaudrate 	= 9600;
    public static int serialDatabits 	= SerialPort.DATABITS_8;
    public static int serialStopbits 	= SerialPort.STOPBITS_1;
    public static int serialParity 		= SerialPort.PARITY_NONE;
	public static double serialTimeout 	= 0.5;
    public static boolean serialXonxoff = false;
    public static boolean serialRtscts	= false;
    public static boolean serialDsrdtr 	= false;
    // end serial port settings

    public static String successSound 	= "snd/LASER.WAV";
	public static String failSound 		= "snd/BUZZ.WAV";
	public static String instrumentID 	= "myInstrumentID";
	public static String emailServer 	= "mailhost.bms.com";
	public static String emailTo 		= "mark.russo@bms.com";
	public static String emailFrom	    = "myInstrumentID@bms.com";
	public static boolean sendEmail 	= false;
}
