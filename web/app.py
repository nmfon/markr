from flask import Flask, request, jsonify
import psycopg2
import xml.etree.ElementTree as ET

app = Flask(__name__)

# Database connection function
def get_db_connection():
    conn = psycopg2.connect(
        dbname='markr',
        user='postgres',
        password='password',
        host='db'
    )
    return conn

# Health check
@app.route('/health')
def index():
    return jsonify({"message": "Service is up"})

# Test database connection
@app.route('/dbtest')
def dbtest():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT version();')
    db_version = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify({"PostgreSQL Version": db_version})

if __name__ == '__main__':
    app.run(host='0.0.0.0')

