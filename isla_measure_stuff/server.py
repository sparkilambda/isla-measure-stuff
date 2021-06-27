from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor
import json
import mimetypes
import os
from typing import Dict
from urllib.request import urlopen
import uuid

from flask import (
    Flask,
    render_template,
)
from flask_sockets import Sockets
import numpy as np

from .euclidean import Line
from .video_creator import MeasurementType, create_video

FILES_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
DOWNLOAD_FILENAME = 'IslaMeasurement.mp4'

app = Flask(__name__)
app.config['FILES_FOLDER'] = FILES_FOLDER
sockets = Sockets(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def editor():
    return render_template('editor.html')


@sockets.route('/generate-video')
def generate_video(ws):
    while not ws.closed:
        message = ws.receive()
        if message is None:
            continue
        data = json.loads(message)

        data_type = data['type']
        if data_type == 'content':
            def process_and_send():
                result = _process_file(data)
                result['type'] = 'content'
                ws.send(json.dumps(result))
                ws.close()
            executor = ThreadPoolExecutor()
            executor.submit(process_and_send)

        if data_type == 'ping':
            ws.send(json.dumps({'type': 'pong'}))


def _process_file(data: Dict) -> Dict:
    file_url = data['file']
    with urlopen(file_url) as response:
        content_type = response.headers['Content-type']
        file_data = response.read()

    file_extension = mimetypes.guess_extension(content_type)
    file_id = uuid.uuid4()
    files_path = app.config['FILES_FOLDER']
    input_file_path = os.path.join(files_path, f'{file_id}-input.{file_extension}')
    output_file_path = os.path.join(files_path, f'{file_id}-output.mp4')

    with open(input_file_path, 'wb') as f:
        f.write(file_data)

    # Get the measurement data
    measure_data = data['measurement']
    measure_type = MeasurementType(measure_data['type'].lower())
    measurement = Line(
        np.array(measure_data['start']),
        np.array(measure_data['end'])
    )

    create_video(
        input_file_path,
        measure_type,
        measurement,
        output_file_path
    )

    with open(output_file_path, 'rb') as f:
        encoded_video = b64encode(f.read()).decode()
        return {
            'filename': DOWNLOAD_FILENAME,
            'file': f'data:video/mp4;base64,{encoded_video}',
        }


if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
