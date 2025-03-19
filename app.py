from flask import Flask, request, send_file
import sqlite3
import pandas as pd
from datetime import datetime, timezone
from flask_cors import CORS  # Add this import

app = Flask(__name__)
CORS(app)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('clicks.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS clicks 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     ad_id TEXT, 
                     timestamp TEXT, 
                     ip_address TEXT)''')
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def home():
    return """
    <h1>Ad Click Tracker API</h1>
    <p>Available endpoints:</p>
    <ul>
        <li>POST /track - Track a click</li>
        <li>GET /clicks - View click data</li>
        <li>GET /download - Download raw data</li>
    </ul>
    """

# Track click endpoint
@app.route('/track', methods=['POST'])
def track_click():
    try:
        data = request.json or {}
        ad_id = data.get('ad_id', 'unknown')
        timestamp = datetime.now(timezone.utc).isoformat()
        ip_address = request.remote_addr  # Capture client IP
        
        print(f"Received click - ad_id: {ad_id}, ip: {ip_address}, time: {timestamp}")  # Debug log
        
        conn = sqlite3.connect('clicks.db')
        cur = conn.cursor()
        
        cur.execute("INSERT INTO clicks (ad_id, timestamp, ip_address) VALUES (?, ?, ?)", 
                    (ad_id, timestamp, ip_address))
        conn.commit()
        
        # Verify the insert worked
        cur.execute("SELECT * FROM clicks WHERE ad_id = ? ORDER BY id DESC LIMIT 1", (ad_id,))
        result = cur.fetchone()
        print(f"Inserted record: {result}")  # Debug log
        
        cur.close()
        conn.close()
        return {"status": "success", "ad_id": ad_id}, 200
    except Exception as e:
        print(f"Error in track_click: {str(e)}")  # Debug log
        return {"error": str(e)}, 500

# API to get aggregated clicks
@app.route('/clicks')
def get_clicks():
    ad_id = request.args.get('ad_id')
    conn = sqlite3.connect('clicks.db')
    query = "SELECT * FROM clicks"
    if ad_id:
        query += " WHERE ad_id = ?"
        df = pd.read_sql_query(query, conn, params=(ad_id,))
    else:
        df = pd.read_sql_query(query, conn)
    conn.close()
    # Basic fraud detection: flag duplicates-This could not be the best way to detect bots
    # df['is_possible_bot'] = df.duplicated(subset=['timestamp', 'ip_address'], keep=False)
    
    # Convert timestamp to datetime for time-based fraud detection
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    # Sort by IP and timestamp
    df = df.sort_values(['ip_address', 'timestamp'])
    
    # Flag clicks within 1 second of the previous click from the same IP-This could not be the best way to detect bots as it is not accurate
    # df['time_diff'] = df.groupby('ip_address')['timestamp'].diff().dt.total_seconds()
    # df['is_possible_bot'] = (df['time_diff'] < 1) | (df['time_diff'].isna() & df.duplicated('ip_address', keep=False))
    # Calculate time difference from previous click
    
    df['time_diff'] = df.groupby('ip_address')['timestamp'].diff().dt.total_seconds()
    # Flag as bot if time_diff is less than 1 second (and not NaN)
    df['is_possible_bot'] = (df['time_diff'] < 1) & (~df['time_diff'].isna())
    df = df.drop(columns=['time_diff'])  # Clean up
    return df.to_json(orient='records')

# Download raw data
@app.route('/download')
def download_raw():
    conn = sqlite3.connect('clicks.db')
    df = pd.read_sql_query("SELECT * FROM clicks", conn)
    conn.close()
    df.to_csv('clicks_raw.csv', index=False)
    return send_file('clicks_raw.csv', as_attachment=True)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)