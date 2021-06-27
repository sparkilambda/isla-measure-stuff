(function () {
  'use strict';

  var form = document.querySelector('.measurement-form');

  var isDragAndDropSupported = function() {
    var div = document.createElement('div');
    return (('draggable' in div) || ('ondragstart' in div && 'ondrop' in div)) && 'FormData' in window && 'FileReader' in window;
  }();

  window.mouseVariable = 'offset';

  // To add a handler to multiple events at the same time
  function addEventsListener(element, eventsString, eventHandler) {
    eventsString.split(' ').forEach(function (eventName) {
      element.addEventListener(eventName, eventHandler);
    });
  }

  // ------------------------------
  // File input
  // ------------------------------
  var fileInput = form.querySelector('.file-input');

  if (isDragAndDropSupported) {
    fileInput.classList.add('has-drag-and-drop')
  }

  addEventsListener(fileInput, 'drag dragstart dragend dragover dragenter dragleave drop', function (ev) {
    // Prevent default behavior (Prevent file from being opened)
    ev.preventDefault();
    ev.stopPropagation();
  });
  addEventsListener(fileInput, 'dragover dragenter', function () {
    fileInput.classList.add('is-dragover');
  });
  addEventsListener(fileInput, 'dragleave dragend drop', function () {
    fileInput.classList.remove('is-dragover');
  });
  addEventsListener(fileInput, 'drop', function (ev) {
    var files = ev.dataTransfer.files;
    if (files && files.length > 0) {
      setImageFile(files[0]);
    }
  });

  // ------------------------------
  // Canvas
  // ------------------------------
  var lineEditor = form.querySelector('.line-editor');
  var editorCanvas = lineEditor.querySelector('canvas');
  var canvasLineStart = null;
  var canvasLineEnd = null;
  var isDrawingLine = false;
  var selectedImageFile = null;
  var selectedImage = null;

  function setImageFile(file) {
    selectedImageFile = file;

    var fr = new FileReader();
    fr.onload = function () {
      var img = new Image();
      img.onload = function () {
        selectedImage = img;
        lineEditor.classList.add('has-file');
        editorCanvas.width = lineEditor.offsetWidth;
        editorCanvas.height = editorCanvas.width * img.height / img.width;
        renderCanvas();
      };
      img.src = fr.result;
    };
    fr.readAsDataURL(file);

    fileInput.classList.add('file-selected');
  }

  function renderCanvas() {
    var ctx = editorCanvas.getContext('2d');
    ctx.drawImage(selectedImage, 0, 0, selectedImage.width, selectedImage.height, 0, 0, editorCanvas.width, editorCanvas.height);
    if (canvasLineStart && canvasLineEnd) {
      ctx.beginPath();
      ctx.moveTo(...canvasLineStart);
      ctx.lineTo(...canvasLineEnd);
      ctx.stroke();
    }
  }

  function getCanvasMousePosition(ev) {
    var x = ev.layerX;
    var y = ev.layerY;
    return [ x, y ];
  }

  editorCanvas.onmousedown = function (ev) {
    if (!isDrawingLine) {
      isDrawingLine = true;
      canvasLineStart = getCanvasMousePosition(ev);
      canvasLineEnd = null;
    } else {
      isDrawingLine = false;
      canvasLineEnd = getCanvasMousePosition(ev);
    }
    renderCanvas();
  }

  editorCanvas.onmousemove = function (ev) {
    if (isDrawingLine) {
      canvasLineEnd = getCanvasMousePosition(ev);
      renderCanvas();
    }
  }

  editorCanvas.onmouseup = function (ev) {
    if (isDrawingLine) {
      var position = getCanvasMousePosition(ev);
      // Drawing line with click and hold
      if (position[0] != canvasLineStart[0] || position[1] != canvasLineStart[1]) {
        canvasLineEnd = position;
        isDrawingLine = false;
      }
    }
  }

  function canvasToImagePosition(canvasPos) {
    var imgPosX = Math.round(canvasPos[0] * selectedImage.width / editorCanvas.width);
    var imgPosY = Math.round(canvasPos[1] * selectedImage.height / editorCanvas.height);
    return [ imgPosX, imgPosY ];
  }

  // ------------------------------
  // Video display
  // ------------------------------
  var videoDisplay = document.querySelector('.video-display');

  function setVideoDisplayContent(src, filename) {
    // Set the video on the video player
    var videoPlayer = videoDisplay.querySelector('video');
    var videoSource = videoPlayer.querySelector('source');
    videoSource.src = src;
    videoPlayer.load();

    // Set the video on the download button
    var downloadButton = videoDisplay.querySelector('a');
    downloadButton.href = src;
    downloadButton.download = filename;
  }

  function setVideoDisplayState(state) {
    videoDisplay.classList.remove('is-loading', 'has-video');
    if (state === 'loading') {
      videoDisplay.classList.add('is-loading');
    } else if (state === 'loaded') {
      videoDisplay.classList.add('has-video');
    }
    setTimeout(function () { videoDisplay.scrollIntoView(); }, 500);
  }

  // ------------------------------
  // Submit
  // ------------------------------
  var ws = null;
  var pingInterval = 15000;
  var pingTimeout = 30000;
  var pingIntervalRef = null;
  var pingTimeoutRef = null;

  form.onsubmit = function (ev) {
    if (form.classList.contains('is-processing')) return false;

    form.classList.add('is-processing');
    setVideoDisplayState('loading');
    ev.preventDefault();

    var ws_scheme = location.protocol === 'https:' ? 'wss://' : 'ws://'
    ws = new WebSocket(ws_scheme + location.host + '/generate-video');

    ws.onopen = onSocketOpen;
    ws.onmessage = onSocketMessage;
    ws.onclose = onSocketClose;
    ws.onerror = onSocketError;
  };

  function sendPing() {
    ws.send('{"type":"ping"}');
    pingTimeoutRef = setTimeout(function () {
      // TODO: ERROR
      ws.close();
    }, pingTimeout);
  }
  window.sendPing = sendPing;

  function receivePong() {
    clearTimeout(pingTimeoutRef);
    pingIntervalRef = setTimeout(sendPing, pingInterval)
  }

  function onSocketOpen() {
    var measurementType = form.querySelector('input[name="measurement-type"]:checked').value;
    var measurementStart = canvasToImagePosition(canvasLineStart);
    var measurementEnd = canvasToImagePosition(canvasLineEnd);

    var fr = new FileReader();
    fr.onload = function () {
      var data = {
        type: 'content',
        file: fr.result,
        measurement: {
          type: measurementType,
          start: measurementStart,
          end: measurementEnd,
        },
      };
      ws.send(JSON.stringify(data));
    };
    fr.readAsDataURL(selectedImageFile);

    pingIntervalRef = setTimeout(sendPing, pingInterval);
  }

  function onSocketMessage(ev) {
    var data = JSON.parse(ev.data);
    if (data.type === 'pong') {
      receivePong();
    }
    if (data.type === 'content') {
      form.classList.remove('is-processing');

      setVideoDisplayContent(data.file, data.filename);
      setVideoDisplayState('loaded');
      ws.close();
    }
  }

  function onSocketClose() {
    form.classList.remove('is-processing');

    clearTimeout(pingIntervalRef);
  }

  function onSocketError() {
    form.classList.remove('is-processing');
    // TODO
  }
})();
