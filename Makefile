.PHONY: setup run-server

PROJECT_FOLDER=isla_measure_stuff


setup:
	pip install -r requirements.txt

run-server:
	FLASK_APP=$(PROJECT_FOLDER)/server.py FLASK_ENV=development flask run
