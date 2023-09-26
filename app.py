from flask import Flask, send_from_directory, render_template, request, Response
from werkzeug.utils import secure_filename
import os
import io
from PIL import Image
import cv2
from ultralytics import YOLO
import argparse
from datetime import datetime  # Import the datetime module
import time

app = Flask(__name__)
intruder_times = []
# Configure a folder for storing uploaded files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Define a function to check and create the uploads folder if it doesn't exist
def create_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

# Define a route for serving the logo.png file
@app.route('/static/logo.png')
def serve_logo():
    return send_from_directory('static', 'logo.png')

# Serve the index.html when accessing the root URL
@app.route('/')
def home():
    return render_template('index.html')

@app.route("/webapp.html", methods=["GET", "POST"])
def predict_img():
    f = None  # Initialize f as None
    num_persons = 0  # Initialize the number of persons detected
    
    intruder = "Perimeter is Secure!"

    if request.method == "POST":
        if 'file' in request.files:
            f = request.files['file']
            basepath = os.path.dirname(__file__)
            filepath = os.path.join(basepath, 'uploads', f.filename)
            print("uploaded folder is ", filepath)
            f.save(filepath)

            file_extension = f.filename.rsplit('.', 1)[1].lower()

            # Initialize the YOLOv8 model here
            model = YOLO('yolov8n.pt')

            if file_extension == 'jpg':
                # Perform the detection
                detections = model.predict(filepath, save=True)  # Will save the image in the "runs" folder
                num_persons = len(detections)  # Get the number of persons detected
                if (num_persons>0):
                    intruder = "INTRUDER DETECTED"
                    intruder_times.append(datetime.now())
                else:
                    intruder = "Perimeter is Secure"
            elif file_extension == 'mp4':
                video_path = filepath
                detections = model.predict(filepath, save=True)  # Will save the image in the "runs" folder
                num_persons = len(detections)  # Get the number of persons detected
                if (num_persons>0):
                    intruder = "INTRUDER DETECTED"
                    intruder_times.append(datetime.now())
                else:
                    intruder = "Perimeter is Secure"

    if f is not None:  # Check if f is defined
        folder_path = 'runs/detect'
        subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
        latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))
        image_path = folder_path + '/' + latest_subfolder + '/' + f.filename
    else:
        image_path = None
    
    return render_template('webapp.html', image_path=image_path, intruder=intruder, intruder_times=intruder_times)

@app.route('/<path:filename>')
def display(filename):
    folder_path = 'runs/detect'
    subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))
    directory = folder_path + '/' + latest_subfolder
    print("printing directory: ", directory)
    
    # List files in the directory
    files = os.listdir(directory)
    
    if not files:
        return "No files found in the directory."
    
    latest_file = files[0]
    filename = os.path.join(folder_path, latest_subfolder, latest_file)
    file_extension = filename.rsplit('.', 1)[1].lower()

    if file_extension == 'jpg':
        return send_from_directory(directory, latest_file)
    elif file_extension == 'avi':
        return send_from_directory(os.getcwd(), filename)
    else:
        return "Invalid file format"
    
@app.route('/missions.html')
def mission():
    return render_template('missions.html')

@app.route('/alerts.html')
def alerts():
    return render_template('alerts.html', intruder_times= intruder_times)

@app.route('/index.html')
def work():
    return render_template('index.html')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask app exposing yolov8 models")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    args = parser.parse_args()
    app.run(debug=True, port=args.port)
