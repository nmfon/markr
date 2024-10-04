import pytest
import json
from flask import Flask
from app import app  # Import the Flask app
from unittest.mock import patch

# Fixture to create a test client
@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Mock database connection for safety in tests
@pytest.fixture
def mock_db_conn():
    with patch('app.get_db_connection') as mock_conn:
        yield mock_conn

# Test /health endpoint
def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'Service is up'

# Test /dbtest endpoint (mocking database)
def test_dbtest(client, mock_db_conn):
    mock_db_conn.return_value.cursor.return_value.fetchone.return_value = ('PostgreSQL 17',)
    response = client.get('/dbtest')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "PostgreSQL Version" in data
    assert data['PostgreSQL Version'] == ['PostgreSQL 17']

# Test /import endpoint with valid XML data (mocking DB)
def test_import_data_valid(client, mock_db_conn):
    mock_cursor = mock_db_conn.return_value.cursor.return_value
    xml_data = """
    <results>
        <mcq-test-result>
            <first-name>John</first-name>
            <last-name>Doe</last-name>
            <student-number>123</student-number>
            <test-id>1</test-id>
            <summary-marks available="100" obtained="80" />
        </mcq-test-result>
    </results>
    """
    response = client.post('/import', data=xml_data, content_type='application/xml')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['message'] == 'Records upserted successfully'
    assert data['processed_records'] == 1

# Test /import endpoint with large student id (mocking DB)
def test_import_data_valid_large_student_id(client, mock_db_conn):
    mock_cursor = mock_db_conn.return_value.cursor.return_value
    xml_data = """
    <results>
        <mcq-test-result>
            <first-name>Bob</first-name>
            <last-name>Smith</last-name>
            <student-number>123456789000000000</student-number>
            <test-id>1</test-id>
            <summary-marks available="100" obtained="80" />
        </mcq-test-result>
    </results>
    """
    response = client.post('/import', data=xml_data, content_type='application/xml')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['message'] == 'Records upserted successfully'
    assert data['processed_records'] == 1

# Test /import endpoint with large test id (mocking DB)
def test_import_data_valid_large_test_id(client, mock_db_conn):
    mock_cursor = mock_db_conn.return_value.cursor.return_value
    xml_data = """
    <results>
        <mcq-test-result>
            <first-name>Bob</first-name>
            <last-name>Smith</last-name>
            <student-number>456</student-number>
            <test-id>999999999999999999</test-id>
            <summary-marks available="100" obtained="80" />
        </mcq-test-result>
    </results>
    """
    response = client.post('/import', data=xml_data, content_type='application/xml')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['message'] == 'Records upserted successfully'
    assert data['processed_records'] == 1

# Test /import endpoint with invalid XML
def test_import_data_invalid_xml(client):
    invalid_xml_data = "<invalid-xml>"
    response = client.post('/import', data=invalid_xml_data, content_type='application/xml')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Failed to parse XML'

# Test /results/<int:test_id>/aggregate with mock data
def test_aggregate_results(client, mock_db_conn):
    mock_cursor = mock_db_conn.return_value.cursor.return_value
    # Mock test data
    mock_cursor.fetchone.side_effect = [(1, 100)]  # Test with marks available
    mock_cursor.fetchall.side_effect = [
        [(1, 123, 80), (1, 456, 90)]  # Results for test_id
    ]

    response = client.get('/results/1/aggregate')
    assert response.status_code == 200
    data = json.loads(response.data)[0]
    assert 'mean' in data
    assert data['mean'] == 85.0
    assert data['stddev'] == pytest.approx(7.1, rel=1e-2)
    assert data['min'] == 80.0
    assert data['max'] == 90.0
    assert data['count'] == 2

# Test /results/<int:test_id>/aggregate with no results
def test_aggregate_results_no_data(client, mock_db_conn):
    mock_cursor = mock_db_conn.return_value.cursor.return_value
    # Mock no results
    mock_cursor.fetchone.side_effect = [(1, 100)]  # Test found
    mock_cursor.fetchall.side_effect = [[]]  # No results

    response = client.get('/results/1/aggregate')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == 'No results found'

# Test /results/<int:test_id>/aggregate with test not found
def test_aggregate_results_test_not_found(client, mock_db_conn):
    mock_cursor = mock_db_conn.return_value.cursor.return_value
    # Mock no test found
    mock_cursor.fetchone.side_effect = [None]

    response = client.get('/results/1/aggregate')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == 'Test not found'

