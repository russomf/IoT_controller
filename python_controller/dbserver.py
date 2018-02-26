# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 17:29:29 2017

@author: russom
"""

import sqlite3, datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Routes
@app.route("/")
def index():
    return app.send_static_file('index.html')

# Route to log a barcode and instrument
@app.route("/log", methods=['POST'])
def log():
    
    try:
        # Get parameters
        barcode    = request.form['BARCODE']
        instrument = request.form['INSTRUMENT_NAME']
        start_time = datetime.datetime.now()    # now
        end_time   = None
        
        # Open database and get a cursor
        cxn = sqlite3.connect('log.sqlite')
        cur = cxn.cursor()
        # Build and execute insert statement
        sql = "INSERT INTO event (BARCODE, INSTRUMENT_NAME, START_TIME, END_TIME) VALUES (?, ?, ?, ?)"
        cur.execute(sql, [barcode, instrument, start_time, end_time])
        
        # Commit and close database. Get auto-generated id.
        cxn.commit()
        id = cur.lastrowid
        cxn.close()
    
        # Assemble and return data
        return jsonify(BARCODE=barcode, INSTRUMENT_NAME=instrument, START_TIME=start_time, END_TIME=end_time, ID=id)
    
    except Exception as ex:
        # Trap and return any errors as JSON
        return jsonify(success=False, msg=repr(ex))
    
# ---
    # Start server
if __name__ == '__main__':
    app.run('0.0.0.0', '7777')
