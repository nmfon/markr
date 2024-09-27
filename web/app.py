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

# Import XML data endpoint with atomic database writes
@app.route('/import', methods=['POST'])
def import_data():
    if not request.data:
        return jsonify({"error": "No data received"}), 400

    try:
        # Parse the XML data
        root = ET.fromstring(request.data)

        # Extract records from the XML
        records = []
        for record in root.findall('mcq-test-result'):
            first_name = record.find('first-name').text 
            last_name = record.find('last-name').text
            student_number = int(record.find('student-number').text)  # Ensure value is an integer
            test_id = int(record.find('test-id').text)  # Ensure value is an integer
            marks_available = int(record.find('summary-marks').get('available'))  # Ensure value is an integer
            marks_obtained = int(record.find('summary-marks').get('obtained'))  # Ensure value is an integer
            records.append((first_name, last_name, student_number, test_id, marks_available, marks_obtained))

        # Open a database connection and start a transaction
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Begin transaction
            for record in records:
                cur.execute(
                    """
                    INSERT INTO students (first_name, last_name, student_number)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (student_number)
                    DO UPDATE SET first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name
                    """,
                    (record[0], record[1], record[2])
                )
                cur.execute(
                    """
                    INSERT INTO tests (test_id, marks_available)
                    VALUES (%s, %s)
                    ON CONFLICT (test_id)
                    DO UPDATE SET marks_available = EXCLUDED.marks_available
                    WHERE tests.marks_available < EXCLUDED.marks_available
                    """,
                    (record[3], record[4])
                )
                cur.execute(
                    """
                    INSERT INTO results (student_number, test_id, marks_obtained)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (test_id, student_number)
                    DO UPDATE SET marks_obtained = EXCLUDED.marks_obtained
                    WHERE results.marks_obtained < EXCLUDED.marks_obtained
                    """,
                    (record[2], record[3], record[5])
                )

            
            # Commit transaction if all queries succeed
            conn.commit()

        except Exception as e:
            # Rollback transaction if any error occurs
            conn.rollback()
            raise e  # Re-raise the exception to return an error response

        finally:
            # Close cursor and connection
            cur.close()
            conn.close()

        return jsonify({"message": "Records upserted successfully", "processed_records": len(records)}), 201

    except ET.ParseError:
        return jsonify({"error": "Failed to parse XML"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0')

