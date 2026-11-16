\set ON_ERROR_STOP on

\connect student_rental_db
\ir sql/rental-listings.sql

CREATE DATABASE student_rental_test_db;
\connect student_rental_test_db
\ir sql/rental-listings.sql
