CREATE TABLE students (
    student_number INTEGER PRIMARY KEY UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255)
);


CREATE TABLE tests (
    test_id INTEGER PRIMARY KEY UNIQUE,
    marks_available INTEGER
);


CREATE TABLE results (
    student_number INTEGER,
    test_id INTEGER,
    marks_obtained INTEGER,
    PRIMARY KEY (student_number, test_id)
);

