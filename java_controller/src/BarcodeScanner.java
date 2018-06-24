/*
 * BarcodeScanner.java
 * 
 * Author: Mark F. Russo, PhD
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

// Serial Port information
// http://rxtx.qbang.org/wiki/index.php/Two_way_communcation_with_the_serial_port
// http://rxtx.qbang.org/wiki/index.php/Discovering_comm_ports
// http://fizzed.com/oss/rxtx-for-java

import java.io.IOException;
import java.io.InputStream;
import java.util.Enumeration;
import gnu.io.CommPort;
import gnu.io.CommPortIdentifier;
import gnu.io.NoSuchPortException;
import gnu.io.PortInUseException;
import gnu.io.SerialPort;
import gnu.io.UnsupportedCommOperationException;

/**
 * BarcodeScanner class to manage barcode scanner
 * @author Mark F. Russo, PhD
 *
 */
public class BarcodeScanner {

	// Input stream of serial port
	private InputStream inStream = null;
	
	/**
	 * BarcodeScanner constructor
	 * @throws Exception 
	 */
	public BarcodeScanner() {
		// Show available ports for convenience
		System.out.println("Ports: ");
		listPorts();
	}
	
	public void disconnect() throws IOException {
		if (inStream != null) {
			inStream.close();
		}
	}
	
	public void connect() throws NoSuchPortException, PortInUseException, UnsupportedCommOperationException, IOException {
		// Open serial port with ThsisSystem parameters
        CommPortIdentifier portId = CommPortIdentifier.getPortIdentifier(ThisSystem.serialPort);
        if ( portId.isCurrentlyOwned() ) {
        	throw( new RuntimeException("Error: Port is currently in use") );
        }
        else
        {
        	String className = this.getClass().getName();
            CommPort commPort = portId.open( className, 2000);
            
            if ( commPort instanceof SerialPort )
            {
                SerialPort serialPort = (SerialPort) commPort;
                //serialPort.enableReceiveThreshold(1);
                serialPort.disableReceiveTimeout();
                serialPort.setSerialPortParams(
                		ThisSystem.serialBaudrate,
                		ThisSystem.serialDatabits,
                		ThisSystem.serialStopbits,
                		ThisSystem.serialParity);
                
                inStream = serialPort.getInputStream();
                //OutputStream outStream = serialPort.getOutputStream();
            }
            else
            {
            	throw( new RuntimeException("Error: Only serial ports are handled by this example.") );
            }
        }
	}
	
	/**
	 * Utility to list available ports
	 */
	public void listPorts()
    {
        @SuppressWarnings("unchecked")
		Enumeration<CommPortIdentifier> port = CommPortIdentifier.getPortIdentifiers();
        while ( port.hasMoreElements() ) 
        {
            CommPortIdentifier portId = port.nextElement();
            System.out.println(portId.getName()  +  " - " +  getPortTypeName(portId.getPortType()) );
        }
    }
    
	/**
	 * Utility to get port name
	 * @param portType The type of port
	 * @return Name of port
	 */
    private String getPortTypeName ( int portType )
    {
        switch ( portType )
        {
            case CommPortIdentifier.PORT_I2C:
                return "I2C";
            case CommPortIdentifier.PORT_PARALLEL:
                return "Parallel";
            case CommPortIdentifier.PORT_RAW:
                return "Raw";
            case CommPortIdentifier.PORT_RS485:
                return "RS485";
            case CommPortIdentifier.PORT_SERIAL:
                return "Serial";
            default:
                return "unknown type";
        }
    }
    
    /**
     * Read the next barcode
     * @return barcode String
     */
    public String readBarcode()
    {
        byte[] buffer = new byte[1024];
        int len = -1;
        String barcode = "";
        
        StringBuilder sb = new StringBuilder();
        try
        {
//        	int avail = inStream.available();
//        	System.out.println(avail);
//        	if ( avail > 0) {
//        		len = this.inStream.read(buffer);
//        		System.out.println(len);
//        		if (len > 0) {
//        			barcode = new String(buffer,0,len);
//        		}
//        	}
        	
        	len = this.inStream.read(buffer);
        	//System.out.println(len);
            while ( len > 0 )
            {
            	String str = new String(buffer,0,len);
                sb.append(str);
                len = this.inStream.read(buffer);
                //System.out.println(len);
            }
        	barcode = sb.toString().trim();
        	//System.out.println(barcode);
        }
        catch ( IOException e )
        {
            e.printStackTrace();
        }
        
        return barcode;
    }
}
