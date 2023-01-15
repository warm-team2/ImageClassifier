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
from file_migrator_mp import file_handling, directory
import random
from flask_dropzone import Dropzone
from threading import Thread



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
    DROPZONE_ALLOWED_FILE_TYPE = 'image',
    DROPZONE_MAX_FILES = 1,
    DROPZONE_DEFAULT_MESSAGE = "",
    # DROPZONE_UPLOAD_BTN_ID='submit1',
    # DROPZONE_UPLOAD_ACTION="result",
    # DROPZONE_IN_FORM=True,
    # DROPZONE_UPLOAD_ON_CLICK=True
)

dropzone = Dropzone(app)


def allowed_file(filename):
    """Функция проверки расширения файла"""
    return (
        "." in filename and filename.rsplit(".", 1)[1].upper() in LIST_OF_IMAGES_SUFFIX
    )


@app.route("/", methods=["GET", "POST"], strict_slashes=False)
def upload_file():
    global answer
    global file_path1
    global data_uploaded
    global probability

    if request.method == "POST":
        true_class = request.form.get("true_prediction")
        if not true_class:            
            if "file" not in request.files:
                message = "Не могу прочитать файл"
                render_template("index.html", message=message)

            file = request.files["file"]
        
            if file.filename == "":
                message = "Нет выбранного файла"
                return render_template("index.html", message=message)

            if file and not allowed_file(file.filename):
                message = "Расширение не поддерживается"
                return render_template("index.html", message=message)

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

        return render_template("index.html")

@app.route("/dl", methods=["GET"], strict_slashes=False)
def down_file():
    return send_from_directory(ful_path, "DS.db")

@app.route("/result", methods=["GET", "POST"], strict_slashes=False)
def result():
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
            
        return render_template("index.html", answer=answer, img_classes=list_of_classes,
                correct_answers=list_of_correct_predictions, answer_picture=file_path1, probability=probability)




if __name__ == "__main__":
    thread = Thread(target=file_handling)
    thread.start()
    app.secret_key = "super secret key"    
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.run(debug=True, host="0.0.0.0")
