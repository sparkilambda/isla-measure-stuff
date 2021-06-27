.PHONY: setup run-server

PROJECT_FOLDER=isla_measure_stuff


setup:
	pip install -r requirements.txt

run-server:
	python -m isla_measure_stuff.server
