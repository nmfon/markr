CREATE TABLE IF NOT EXISTS students (
    student_number BIGINT PRIMARY KEY UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255)
);


CREATE TABLE IF NOT EXISTS tests (
    test_id BIGINT PRIMARY KEY UNIQUE,
    marks_available INTEGER
);


CREATE TABLE IF NOT EXISTS results (
    student_number BIGINT,
    test_id BIGINT,
    marks_obtained INTEGER,
    PRIMARY KEY (student_number, test_id)
);


/* Performance improvements for aggregate calculations */

ALTER TABLE tests
    ADD COLUMN results_count BIGINT
    ADD COLUMN marks_sum BIGINT
    ADD_COLUMN marks_variance NUMERIC
    ADD_COLUMN marks_stddev NUMERIC;

--ALTER TABLE tests
--    ADD COLUMN marks_frequency BIGINT[];

