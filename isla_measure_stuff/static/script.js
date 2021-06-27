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
      }
      img.src = fr.result;
    }
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
    console.log(ev);
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
  }

  // ------------------------------
  // Submit
  // ------------------------------
  form.onsubmit = function (ev) {
    if (form.classList.contains('is-processing')) return false;

    form.classList.add('is-processing');
    setVideoDisplayState('loading');
    window.scrollTo(0, document.body.scrollHeight);
    ev.preventDefault();

    var data = new FormData(form);

    // The file input actually comes empty because it is hidden,
    // so we replace it's value with the actual file.
    var fileKey = fileInput.querySelector('input').name;
    data.delete(fileKey);
    data.append(fileKey, selectedImageFile);

    var measurementStart = canvasToImagePosition(canvasLineStart);
    var measurementEnd = canvasToImagePosition(canvasLineEnd);

    data.append('measurement-start-x', measurementStart[0]);
    data.append('measurement-start-y', measurementStart[1]);
    data.append('measurement-end-x', measurementEnd[0]);
    data.append('measurement-end-y', measurementEnd[1]);

    var request = new XMLHttpRequest();
    request.open(form.method, form.action);
    request.responseType = 'blob';
    request.onload = function () {
      form.classList.remove('is-processing');
      videoDisplay.classList.remove('is-loading');

      var status = request.status;
      if (status === 0 || (status >= 200 && status < 400)) {
        var blob = request.response;
        var contentDisposition = request.getResponseHeader('Content-Disposition');
        var filename = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)[1];
        setVideoDisplayContent(window.URL.createObjectURL(blob), filename);
        setVideoDisplayState('loaded');
        window.scrollTo(0, document.body.scrollHeight);
      } else {
        // TODO
      }
    }
    request.send(data);
  };
})();
