import os
from typing import Dict
import uuid

from flask import (
    flash,
    Flask,
    redirect,
    render_template,
    request,
    send_file,
)
import numpy as np
from werkzeug.datastructures import FileStorage

from .constants import (
    ALLOWED_EXTENSIONS,
    DOWNLOAD_FILENAME,
    RESULTS_TTL,
    SERVER_FILES_FOLDER,
)
from .euclidean import Line
from .polling_worker import PollingWorker
from .video_creator import MeasurementType, create_video


app = Flask(__name__)
app.config['FILES_FOLDER'] = SERVER_FILES_FOLDER
worker = PollingWorker(target=create_video)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def editor():
    return render_template('editor.html')


@app.route('/generate-video', methods=['POST'])
def generate_video():
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        execution_id = _process_file(file, request.form.to_dict())

        return execution_id, 202


@app.route('/get-video/<execution_id>')
def get_video(execution_id: str):
    if worker.is_done(execution_id):
        output_file_path = worker.get_result(execution_id)
        return send_file(output_file_path, download_name=DOWNLOAD_FILENAME, as_attachment=True)
    else:
        return '', 204


def _process_file(file: FileStorage, payload: Dict) -> str:
    file_extension = file.filename.rsplit('.', 1)[1]
    file_id = uuid.uuid4()
    files_path = app.config['FILES_FOLDER']
    input_file_path = os.path.join(files_path, f'{file_id}-input.{file_extension}')
    output_file_path = os.path.join(files_path, f'{file_id}-output.mp4')

    file.save(input_file_path)

    # Get the measurement data
    measure_type = MeasurementType(payload.get('measurement-type').lower())
    measurement = Line(
        np.array([int(payload.get('measurement-start-x')), int(payload.get('measurement-start-y'))]),
        np.array([int(payload.get('measurement-end-x')), int(payload.get('measurement-end-y'))])
    )

    execution_id = worker.process(
        RESULTS_TTL,
        input_file_path,
        measure_type,
        measurement,
        output_file_path
    )

    return execution_id
