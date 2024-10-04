from flask import Flask, request, jsonify
import json
import logging
import os
import psycopg2
import statistics
import xml.etree.ElementTree as ET

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# Database connection function
def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('DATABASE_NAME'),
        user=os.getenv('DATABASE_USER'),
        password=os.getenv('DATABASE_PASSWORD'),
        host=os.getenv('DATABASE_HOST')
    )
    return conn

# Health check
@app.route('/health')
def index():
    app.logger.info('%s: service is up', request.path)
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
    app.logger.info('%s: db is up', request.path)
    return jsonify({"PostgreSQL Version": db_version})

# Import XML data endpoint with atomic database writes
@app.route('/import', methods=['POST'])
def import_data():
    if not request.data:
        app.logger.error('%s: no data received to import', request.path)
        return jsonify({"error": "No data received to import"}), 400

    try:
        # Parse the XML data
        root = ET.fromstring(request.data)
        app.logger.info('%s: parsed xml data for import', request.path)

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
        app.logger.info('%s: opening connection to database', request.path)
        conn = get_db_connection()
        cur = conn.cursor()
        app.logger.info('%s: connected to database', request.path)

        try:
            # Begin transaction
            for record in records:
                app.logger.info('%s: starting import of record into db %s', request.path, json.dumps({
                    "first_name":record[0],
                    "last_name":record[1],
                    "student_number":record[2],
                    "test_id":record[3],
                    "marks_available":record[4],
                    "marks_obtained":record[5]
                }))

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

            app.logger.info('%s: finished import of record into db %s', request.path, json.dumps({
                 "first_name":record[0],
                 "last_name":record[1],
                 "student_number":record[2],
                 "test_id":record[3],
                 "marks_available":record[4],
                 "marks_obtained":record[5]
            }))

        except Exception as e:
            # Rollback transaction if any error occurs
            conn.rollback()
            raise e  # Re-raise the exception to return an error response

        finally:
            # Close cursor and connection
            app.logger.info('%s: closing connection to database', request.path)
            cur.close()
            conn.close()
            app.logger.info('%s: disconnected from database', request.path)

        return jsonify({"message": "Records upserted successfully", "processed_records": len(records)}), 201

    except ET.ParseError:
        app.logger.error('%s: failed to parse xml for import', request.path)
        return jsonify({"error": "Failed to parse XML"}), 400

    except Exception as e:
        app.logger.error('%s: %s', request.path, str(e))
        return jsonify({"error": str(e)}), 500

# Fetch aggregate results of a test endpoint
@app.route('/results/<int:test_id>/aggregate', methods=['GET'])
def aggregate_results(test_id):
    try:
        # Connect to the database
        app.logger.info('%s: opening connection to database', request.path)
        conn = get_db_connection()
        cur = conn.cursor()
        app.logger.info('%s: connected to database', request.path)

        try:
            # Fetch test by test_id
            app.logger.info('%s: fetching test %s', request.path, test_id)
            cur.execute("SELECT test_id, marks_available FROM tests WHERE test_id = %s", (test_id,))
            test = cur.fetchone()

            # Fetch results by test_id
            app.logger.info('%s: fetching results for test %s', request.path, test_id)
            cur.execute("SELECT test_id, student_number, marks_obtained FROM results WHERE test_id = %s", (test_id,))
            results = cur.fetchall()

        except Exception as e:
            raise e  # Re-raise the exception to return an error response

        finally:
            # Close cursor and connection
            app.logger.info('%s: closing connection to database', request.path)
            cur.close()
            conn.close()
            app.logger.info('%s: disconnected from database', request.path)

        # Check if test was found
        if test:
            app.logger.info('%s: found test %s', request.path, test_id)
            marks_available = test[1]
        else:
            app.logger.error('%s: test %s not found', request.path, test_id)
            return jsonify({"error": "Test not found"}), 404

        # Check if any results were found
        if results:
            app.logger.info('%s: found %s results for test %s', request.path, len(results), test_id)
            marks = [item[2] for item in results]

            min_mark = min(marks) / marks_available * 100
            max_mark = max(marks) / marks_available * 100

            mean = statistics.mean(marks) / marks_available * 100

            # Calculate standard deviation (requires 2 or more results)
            if len(results) >= 2:
                standard_deviation = statistics.stdev(marks) / marks_available * 100
            else:
                standard_deviation = 0.0

            # Calculate percentiles (requires 2 or more results)
            if len(results) >= 2 :
                percentiles = statistics.quantiles(marks)

                percentile25 = percentiles[0] / marks_available * 100
                percentile50 = percentiles[1] / marks_available * 100
                percentile75 = percentiles[2] / marks_available * 100
            else:
                percentile25 = marks[0]
                percentile50 = marks[0]
                percentile75 = marks[0]

            # Return aggregate results as a JSON response
            return jsonify([
                {
                    "mean": round(mean, 1),
                    "stddev": round(standard_deviation, 1),
                    "min": round(min_mark, 1),
                    "max": round(max_mark, 1),
                    "p25": round(percentile25, 1),
                    "p50": round(percentile50, 1),
                    "p75": round(percentile75, 1),
                    "count": len(results)
                }
            ]), 200
        else:
            app.logger.error('%s: no results found for test %s', request.path, test_id)
            return jsonify({"error": "No results found"}), 404

    except Exception as e:
        app.logger.error('%s: %s', request.path, str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0')

