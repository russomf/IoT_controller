/*
 * Controller.java
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

import java.io.*;
import javax.sound.sampled.*;
import java.util.Properties;
import java.util.logging.*;
import java.net.HttpURLConnection;
import java.net.URL;
import javax.mail.Message;
import javax.mail.Session;
import javax.mail.Transport;
import javax.mail.internet.InternetAddress; 
import javax.mail.internet.MimeMessage; 
import org.json.simple.JSONObject;			// See https://code.google.com/archive/p/json-simple/
import org.json.simple.parser.JSONParser;

/**
 * Main controller class
 * @author Mark F. Russo, PhD
 *
 */
public class Controller {

	// BlinkStick object
	private BlinkStick _bs = null;
	
	// Barcode Scanner object
	private BarcodeScanner _scanner = null;
	
	// Sound clip objects
	private static Clip _ping = null;
	private static Clip _buzz = null;
	
	// Logger object
	public static Logger logger = null;

	/**
	 * Controller constructor
	 */
	public Controller() {
		
		// Find blinkstick
		logger.info("Initializing BlinkStick.");
		_bs = BlinkStick.findFirst();
		
		if (_bs == null) {
			logger.warning("Blinkstick not found" );
		}
		
		// Create barcode scanner
		logger.info("Initializing Barcode Reader.");
		try {
			_scanner = new BarcodeScanner();
			_scanner.connect();
		} catch (Exception ex) {
			logger.warning(ex.getClass().getSimpleName() + ": " + ex.getMessage());
		}
		
		// Load sound clips
		try {
			File filSuccess = new File(ThisSystem.successSound);
			AudioInputStream aisSuccess = AudioSystem.getAudioInputStream(filSuccess);              
			_ping = AudioSystem.getClip();
			_ping.open(aisSuccess);
			
			File filFail = new File(ThisSystem.failSound);
			AudioInputStream aisFail = AudioSystem.getAudioInputStream(filFail);              
			_buzz = AudioSystem.getClip();
			_buzz.open(aisFail);
			
		} catch (IOException | UnsupportedAudioFileException | LineUnavailableException e) {
			logger.log(Level.WARNING, "One or more sounds not initialized: {0}", e );
		}
	}
    
	/**
	 * BlinkStick startup sequence
	 */
	private void startup() {
		this.startup(50);
	}
	private void startup(long delay) {
		// Reset and play startup sound
		ping();
		
		try {
			if (_bs != null) {
				// Turn off all LEDs
				off();
			
				// Play startup sequence
				for (int i=0; i<8; ++i) {
					_bs.setIndexedColor(i, 0x0000FF);
					Thread.sleep(delay);
				}
			}
		} catch(InterruptedException e) {
			// Ignore
		}
	}

	/**
	 * BlinkStick success sequence
	 */
	private void success() {
		this.success(10, 500);
	}
	private void success(long delay, long hold) {
		ping();
		
		try {
			for (int i=0; i<8; ++i) {
				_bs.setIndexedColor(i, 0x00FF00);
				Thread.sleep(delay);
			}
			
			Thread.sleep(hold);
	
			for (int i=0; i<8; ++i) {
				_bs.setIndexedColor(i, 0x0000FF);
				Thread.sleep(delay);
			}
		} catch(InterruptedException e) {
			// Ignore
		}
	            		
	}
	
	/**
	 * BlinkStick failure sequence
	 */
	private void fail() {
		this.fail(10);
	}
	private void fail(long delay) {
		buzz();
		
		try {
			for (int i=0; i<8; ++i) {
				_bs.setIndexedColor(i, 0xFF0000);
				Thread.sleep(delay);
			}
		} catch(InterruptedException e) {
			// Ignore
		}
	}
	
	/**
	 * BlinkStick lights off
	 */
	private void off()
	{
		try {
			if (_bs != null) {
				// Turn off all LEDs
				for (int i=0; i<8; ++i) {
					_bs.setIndexedColor(i, 0x000000);
					Thread.sleep(1);
				}
			}
		} catch(InterruptedException e) {
			// Ignore
		}
	}
	
	/**
	 * Post event to log URL and return log ID
	 * @param barcode		Barcode read
	 * @param instrument 	Name of instrument
	 * @return				ID of log record
	 */
	private long log(String barcode, String instrument) {

		try {
			
			URL url = new URL(ThisSystem.log_url);
			HttpURLConnection cxn = (HttpURLConnection) url.openConnection();
			cxn.setRequestMethod("POST");
			cxn.setDoOutput(true);
			cxn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
			cxn.setRequestProperty("Accept-Language", "en-US,en;q=0.5");
			
			String data = "BARCODE=" + barcode + "&INSTRUMENT_NAME=" + ThisSystem.instrumentID;
			OutputStreamWriter out = new OutputStreamWriter(cxn.getOutputStream());
			out.write(data);
			out.flush();
			out.close();
			
			int code = cxn.getResponseCode();
			if (code >= 200 && code < 300) {
			
				BufferedReader in = new BufferedReader( new InputStreamReader(cxn.getInputStream()));
				StringBuffer resp = new StringBuffer();
	
				String line;
				while ((line = in.readLine()) != null) { resp.append(line); }
				in.close();
				
				JSONParser parser = new JSONParser();
				JSONObject respdata = (JSONObject)(parser.parse(resp.toString()));
				@SuppressWarnings("unchecked")
				long id = (long)respdata.getOrDefault("ID", -1L);

				success();
				return id;
				
			} else {
				logger.severe("HTTP request failed: code="+code);
				fail();
				return -1L;
			}
			
		} catch (Exception ex) {
			logger.severe(ex.getClass().getSimpleName() + ": " + ex.getMessage());
			fail();
			return -1L;
		}
	}
	
	/**
	 *  Play success sound
	 */
	private void ping() {
		_ping.stop();
		_ping.flush();
		_ping.setFramePosition(0);
		_ping.start();
	}
	
	/**
	 *  Play fail sound
	 */
	private void buzz() {
		_buzz.stop();
		_buzz.flush();
		_buzz.setFramePosition(0);
		_buzz.start();
	}
	
	/**
	 * Private utility for obtaining computer name
	 * @return computer name String
	 */
	private String getComputerName() {
	    String computerName = "";
	    try {
	    	computerName = java.net.InetAddress.getLocalHost().getHostName();
	    } catch (java.net.UnknownHostException ex) {
	      logger.warning("Hostname can not be resolved");
	    }
	    return computerName;
	}
	
	/**
	 * Utility to send email
	 * @param message The message to be sent
	 * @see https://javaee.github.io/javamail/
	 */
	private void sendEmail(String message)
	{
		// Only send email if setting is true
		if (ThisSystem.sendEmail) {
			Properties props = new Properties();
			props.put("mail.smtp.host", ThisSystem.emailServer);
			props.put("mail.smtp.port", "25");
			props.put("mail.smtp.starttls.enable", "true");
			
			Session session  = Session.getDefaultInstance( props , null);
			String to = ThisSystem.emailTo;
			String from = ThisSystem.emailFrom;
			String subject = "Error message from " + ThisSystem.instrumentID + ". computer : " + getComputerName();
			Message msg = new MimeMessage(session);
			try {
				msg.setFrom(new InternetAddress(from));
				msg.setRecipient(Message.RecipientType.TO , new InternetAddress(to));
				msg.setSubject(subject);
				msg.setText(message);
				Transport.send(msg);
			}  catch(Exception ex) {
				logger.warning(ex.getClass().getSimpleName() + ": " + ex.getMessage());
			}
		}
	}
	
	/**
	 *  Run the controller main loop
	 */
	public void runController() {

		// Startup BlinkStick sequence
		startup();
		
		try {
			logger.info("Controller running");
			
			// Continue until user hits keyboard
			while(System.in.available() == 0) {
				
				// Read the next bar code
				String barcode = _scanner.readBarcode();
				if (barcode.length() > 0) {  
	                long ID = log(barcode, ThisSystem.instrumentID);
	                logger.info("Barcode : " + barcode +  " ID returned from server : " + ID);  
				}
			}
			_scanner.disconnect();
			
		} catch (Exception ex) {
			String msg = this.getClass().getSimpleName() + ": " + ex.getMessage();
			logger.severe(msg);
			sendEmail(msg);
		}
				
		// Turn off BlinkStick
		off();
		logger.info("Controller Stopped.");
	}
	
	/**
	 *  Create new controller object and run main loop
	 * @param args Command line args. Unused.
	 */
	public static void main(String[] args) {
		
		// Configure logging handlers
		logger = Logger.getLogger(Controller.class.getName());
		SimpleFormatter formatter = new SimpleFormatter();
		
		try {
			Handler handler1 = new FileHandler("log.%u.%g.txt", 1024 * 1024, 10, true);
			handler1.setFormatter(formatter);
			logger.addHandler( handler1 );
			
			// Create and start the controller
			Controller ctrl = new Controller();
			ctrl.runController();
			
		} catch (SecurityException | IOException e1) {
			e1.printStackTrace();
		}
	}
}
