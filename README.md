# Markr

A web service for ingesting and reporting on exam results.

## Assumptions for this Prototype

For the purposes of developing a prototype for this web service, the following assumptions have been made:

- any specific container orchestration technologies for production are yet to be determined (and can be addressed largely independently of the specific implementation of this prototype, due to its simple design)
- a single-node database is sufficient for developing and testing this prototype
- the format of the XML payload sent to the `/import` endpoint is as per the example in the requirements
- the format of the JSON response returned by the `/results/<test-id>/aggregate` endpoint is as per the example in the requirements, which contains a few additional fields than are stated in the paragraph above the example
- the requirement of no SSL/TLS for this web service is not a joke (and should be addressed before releasing to production)

## Solution Overview

This web service has been implemented in python 3, using the [Flask](https://github.com/pallets/flask) framework.

The backend is a Postgres relational database, with the following tables:

- students
- tests
- results

For local development, the web service is packaged into a Docker image and run using Docker Compose, which provisions the following containers:

- markr-web (the web service)
- markr-db (the backend, a Postgres database)

The above design and technologies have been chosen to ensure the solution is:

- simple
- lightweight
- extensible
- maintainable
- portable

## Development

### Pre-requisites

Ensure you have the following packages installed on your local machine:

- docker
- docker-compose
- git
- python3
- pytest
- pytest-cov

### Building

To build and run the markr web service locally:

```bash
- git clone git@github.com:nmfon/markr.git
- cd markr
- docker compose up --build
```

To stop the markr web service locally:

```bash
docker compose down
```

To tear down the markr web service (including the data volume for Postgres) locally:

```bash
docker compose down -v
```

### Testing

To run the included test suite:

```bash
pip install --user -r web/requirements.txt
pip install --user -r web/requirements-test.txt
pytest -v --cov web
```

