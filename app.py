from time import sleep

from sqlalchemy import create_engine
from flask import Flask, render_template, request, redirect, send_from_directory, url_for
import numpy as np
import shutil
import tensorflow as tf
from tensorflow import keras
import pathlib as pl
import os
from sqlalchemy.orm import sessionmaker
from werkzeug.utils import secure_filename
from models import GoogleFiles, create_db
import random
from flask_dropzone import Dropzone
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

directory = "static"
FOLDER_ID = ""

current_path = os.getcwd()
ful_path = os.path.abspath(current_path)
UPLOAD_FOLDER = os.path.abspath(os.path.join(ful_path, directory))
LIST_OF_IMAGES_SUFFIX = ["JPEG", "PNG", "JPG", "SVG"]
CLASS_DICT = {
    0: "airplane",
    1: "automobile",
    2: "bird",
    3: "cat",
    4: "deer",
    5: "dog",
    6: "frog",
    7: "horse",
    8: "ship",
    9: "truck",
    10: "other",
}



answer = "other"
data_uploaded = False
probability = 0
inv_class_dict = {value: key for key, value in CLASS_DICT.items()}
list_of_classes = list(CLASS_DICT.values())
list_of_correct_predictions = ["true", "false"]
chars = "abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"


def f1_m(y_true, y_pred):
    pass

def precision_m(y_true, y_pred):
    pass


def recall_m(y_true, y_pred):
    pass

create_db()
img_clas = keras.models.load_model(
    "model1.h5",
    custom_objects={"f1_m": f1_m, "precision_m": precision_m, "recall_m": recall_m},
)

engine = create_engine("sqlite:///DS.db", connect_args={"check_same_thread": False})
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__, static_folder=UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config.update(
    UPLOADED_PATH=UPLOAD_FOLDER,
    DROPZONE_MAX_FILE_SIZE = 1024,
    DROPZONE_TIMEOUT = 5*60*1000,
    DROPZONE_ALLOWED_FILE_CUSTOM = True,
    DROPZONE_ALLOWED_FILE_TYPE = '.JPEG, .PNG, .JPG, .SVG, jpeg, .png, jpg, .svg',
    DROPZONE_MAX_FILES = 1,
    DROPZONE_DEFAULT_MESSAGE = ""
)

dropzone = Dropzone(app)


def allowed_file(filename):
    """?????????????? ???????????????? ???????????????????? ??????????"""
    return (
        "." in filename and filename.rsplit(".", 1)[1].upper() in LIST_OF_IMAGES_SUFFIX
    )


@app.route("/", methods=["GET", "POST"], strict_slashes=False)
def upload_file():

    user_agent = request.headers.get('User-Agent')
    user_agent = user_agent.lower()

    if ("iphone" in user_agent) or ("android" in user_agent):
        index = "mobile.index.html"
    else:
        index = "index.html"

    global answer
    global file_path1
    global data_uploaded
    global probability

    if request.method == "POST":
        true_class = request.form.get("true_prediction")
        if not true_class:            
            if "file" not in request.files:
                message = "???? ???????? ?????????????????? ????????"
                render_template(index, message=message)

            file = request.files["file"]
        
            if file.filename == "":
                message = "?????? ???????????????????? ??????????"
                return render_template(index, message=message)

            if file and not allowed_file(file.filename):
                message = "???????????????????? ???? ????????????????????????????"
                return render_template(index, message=message)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename.rsplit(".", 1)[0].lower())
                exist_filename = (
                    session.query(GoogleFiles)
                    .filter(
                        GoogleFiles.file_name == file.filename.rsplit(".", 1)[0].lower()
                    )
                    .first()
                )
                if exist_filename:
                    add_chars = ""
                    for n in range(10):
                        add_chars += random.choice(chars)
                    filename += add_chars

                file.save(
                    os.path.join(
                        UPLOAD_FOLDER, filename + "." + file.filename.rsplit(".", 1)[1]
                    )
                )

                file_record_google = GoogleFiles(
                    file_name=filename,
                    file_extension=file.filename.rsplit(".", 1)[1],
                )

                session.add(file_record_google)
                session.commit()
                global recorded_file
                recorded_file = (
                    session.query(GoogleFiles)
                    .filter(GoogleFiles.file_name == filename)
                    .first()
                )
                file_path = os.path.join(
                    UPLOAD_FOLDER, f"{filename}.{file.filename.rsplit('.', 1)[1]}"
                )
                image = tf.keras.utils.load_img(file_path, target_size=(32, 32, 3))
                if image:
                    input_arr = tf.keras.utils.img_to_array(image)
                    input_arr = np.array([input_arr/255])
                    prediction = img_clas.predict(input_arr)

                    global answer
                    #global answer_picture
                    global file_path1
                    global probability

                    prediction = list(prediction)
                    probability = prediction[0][np.argmax(prediction)]
                    message = f"Probability is {round(probability*100, 0)}%"
                    answer_picture = f"{directory}/cifar_images/{CLASS_DICT[np.argmax(prediction)]}.png"
                    file_path1 = (
                        f"{directory}/{filename}.{file.filename.rsplit('.', 1)[1]}"
                    )
                    if probability > 0.5:
                        answer = CLASS_DICT[np.argmax(prediction)]
                        print(f"Answer is {answer}")

                    else:
                        answer = "other"

                        print(f"Answer is {answer}")
                    
                    data_uploaded = True    
                    return "." 

    if request.method == "GET":
        data_uploaded = False
        answer = None
        probability = 0
        file_path1 = None

        return render_template(index)

@app.route("/dl", methods=["GET"], strict_slashes=False)
def down_file():
    return send_from_directory(ful_path, "DS.db")

@app.route("/result", methods=["GET", "POST"], strict_slashes=False)
def result():

    user_agent = request.headers.get('User-Agent')
    user_agent = user_agent.lower()

    if ("iphone" in user_agent) or ("android" in user_agent):
        index = "mobile.index.html"
    else:
        index = "index.html"


    if request.method == "POST":
        true_class = request.form.get("true_prediction")
        if true_class == "true":

            recorded_file.pred = True
            recorded_file.img_class = int(inv_class_dict[answer])
            session.add(recorded_file)
            session.commit()
            return redirect("/")

        elif true_class == "false":
            recorded_file.pred = False
            real_class = request.form.get("true_class")
            real_class = inv_class_dict[real_class]
            real_class = int(real_class)
            recorded_file.img_class = real_class
            session.add(recorded_file)
            session.commit()
            return redirect("/")
    else:

        while not data_uploaded :
            pass
            
        return render_template(index, answer=answer, img_classes=list_of_classes,
                correct_answers=list_of_correct_predictions, answer_picture=file_path1, probability=probability)

@app.route("/dg", methods=["GET"], strict_slashes=False)
def send_to_google_file():
    global gauth
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("mycreds.txt")
    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()
    # Save the current credentials to a file
    gauth.SaveCredentialsFile("mycreds.txt") 

    current_path = os.getcwd()
        
    global drive
    drive = GoogleDrive(gauth)

    folderlist = drive.ListFile(
                {"q": "mimeType='application/vnd.google-apps.folder' and trashed=false"}
            ).GetList()
    titlelist = [x["title"] for x in folderlist]

    if directory not in titlelist:
        folder_metadata = {
                "title": directory,
                "mimeType": "application/vnd.google-apps.folder",
            }
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()

    folderlist1 = drive.ListFile(
                {"q": "mimeType='application/vnd.google-apps.folder' and trashed=false"}
            ).GetList()
    titlelist1 = [x for x in folderlist1]

    for item in titlelist1:    
        if str(item["title"]) == "static":
            global folder_id
            folder_id = item["id"]

    google_files = session.query(GoogleFiles).all()
    os.chdir(UPLOAD_FOLDER)    
    for google_file in google_files: 
        
        if not google_file.file_id:                         
            #print(os.getcwd())
            gfile = drive.CreateFile(
                        {"parents": [{"kind": "drive#fileLink", "id": folder_id}]}
                    )
            gfile.SetContentFile(f"{google_file.file_name}.{google_file.file_extension}")
            gfile.Upload()    
    os.chdir(current_path)
    return redirect("/")

@app.route("/gd", methods=["GET"], strict_slashes=False)   
def send_from_google_disk_to_DB():    
    new_fileList = drive.ListFile({"q": f"'{folder_id}' in parents and trashed=false"}).GetList()        
    google_files1 = session.query(GoogleFiles).all()
    for google_file1 in google_files1:
        if not google_file1.file_id:            
            for files in new_fileList:
                    #print(files["title"])
                if files["title"] == f"{google_file1.file_name}.{google_file1.file_extension}":                    
                    google_file1.file_id = files["id"]       
                    session.add(google_file1)
                    session.commit()
    return redirect("/")

@app.route("/del", methods=["GET"], strict_slashes=False)   
def del_files():
    google_files2 = session.query(GoogleFiles).all()
    for google_file2 in google_files2:       
        item_path=os.path.join(UPLOAD_FOLDER, f"{google_file2.file_name}.{google_file2.file_extension}")
        path = pl.Path(item_path)
        if google_file2.file_id and path.exists():         
            try:
                os.remove(path)
            except PermissionError:
                print(f"trying to delete  {google_file2.file_name}.{google_file2.file_extension}")
                os.chdir(current_path)
                return redirect("/")        
    return redirect("/")


if __name__ == "__main__":
    #thread = Thread(target=file_handling)
    #thread.start()
    app.secret_key = "super secret key"    
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.run(debug=True, host="0.0.0.0")
