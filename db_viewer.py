#!/usr/bin/env python3
"""
Database Web Viewer
A simple web interface to view the media pipeline database
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Add the project directory to Python path
project_dir = "/opt/media-pipeline"
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

try:
    from flask import Flask, render_template, jsonify, request
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
    from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

class DatabaseViewer:
    """Database viewer for media pipeline"""
    
    def __init__(self):
        self.db_path = "/opt/media-pipeline/media.db"
        self.project_dir = "/opt/media-pipeline"
    
    def get_tables(self):
        """Get all tables in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tables
        except Exception as e:
            return []
    
    def get_table_data(self, table_name, limit=100):
        """Get data from a specific table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Get data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            rows = cursor.fetchall()
            
            conn.close()
            
            return {
                "columns": columns,
                "rows": rows,
                "count": len(rows)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_table_count(self, table_name):
        """Get row count for a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            return 0
    
    def execute_query(self, query):
        """Execute a custom SQL query"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                conn.close()
                return {
                    "columns": columns,
                    "rows": rows,
                    "count": len(rows)
                }
            else:
                conn.commit()
                conn.close()
                return {"message": "Query executed successfully"}
        except Exception as e:
            return {"error": str(e)}

# Global database viewer
db_viewer = DatabaseViewer()

@app.route('/')
def index():
    """Main database viewer page"""
    return render_template('db_viewer.html')

@app.route('/api/tables')
def get_tables():
    """API endpoint to get all tables"""
    tables = db_viewer.get_tables()
    table_info = []
    for table in tables:
        count = db_viewer.get_table_count(table)
        table_info.append({"name": table, "count": count})
    return jsonify(table_info)

@app.route('/api/table/<table_name>')
def get_table_data(table_name):
    """API endpoint to get table data"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify(db_viewer.get_table_data(table_name, limit))

@app.route('/api/query', methods=['POST'])
def execute_query():
    """API endpoint to execute custom queries"""
    data = request.get_json()
    query = data.get('query', '')
    return jsonify(db_viewer.execute_query(query))

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(project_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    print("Starting Database Viewer...")
    print("Database Viewer will be available at: http://0.0.0.0:8084")
    print("Press Ctrl+C to stop")
    
    # Run the Flask app
    # Check for PORT environment variable (PM2 override)
    port = int(os.environ.get('PORT', 8084))
    app.run(host='0.0.0.0', port=port, debug=False)
