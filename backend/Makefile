# Makefile — shortcuts cho dev workflow
# Dùng: make test | make test-cov | make test-unit | make test-api

.PHONY: test test-unit test-api test-trainer test-cov lint install-dev

# Cài đặt dependencies (bao gồm test)
install-dev:
	pip install -r requirements.txt

# Chạy toàn bộ test
test:
	pytest

# Chỉ test unit (nhanh, không cần network)
test-unit:
	pytest tests/test_preprocessing.py tests/test_model.py tests/test_dataset.py -v

# Test scraper (có mock)
test-scraper:
	pytest tests/test_scraper.py -v

# Test API endpoints
test-api:
	pytest tests/test_api.py -v

# Test trainer logic
test-trainer:
	pytest tests/test_trainer.py -v

# Chạy với coverage report
test-cov:
	pytest --cov=src --cov=api --cov-report=term-missing --cov-report=html:logs/coverage

# Xem coverage HTML report
cov-open:
	start logs/coverage/index.html
