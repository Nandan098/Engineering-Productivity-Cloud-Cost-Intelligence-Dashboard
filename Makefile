.PHONY: install validate analyze dashboard test

install:
	python -m pip install -r requirements.txt

validate:
	python src/validate_data.py

analyze:
	python src/run_analysis.py

dashboard:
	streamlit run app/Home.py

test:
	pytest -q
