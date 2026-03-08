# Tests Directory

This directory contains all backend tests using pytest.

## Structure

- `test_auth.py` - Authentication and user management tests
- `test_academic.py` - Course, department, semester tests
- `test_timetable.py` - Timetable generation tests
- `conftest.py` - Pytest fixtures and configuration

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```
