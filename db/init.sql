CREATE TABLE students (
    student_number BIGINT PRIMARY KEY UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255)
);


CREATE TABLE tests (
    test_id BIGINT PRIMARY KEY UNIQUE,
    marks_available INTEGER
);


CREATE TABLE results (
    student_number BIGINT,
    test_id BIGINT,
    marks_obtained INTEGER,
    PRIMARY KEY (student_number, test_id)
);

