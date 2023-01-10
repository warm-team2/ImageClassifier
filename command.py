from sqlalchemy import create_engine
from flask import Flask, render_template, request, redirect, send_from_directory
import numpy as np
import shutil
import tensorflow as tf
from tensorflow import keras
import pathlib as pl
import os
from sqlalchemy.orm import sessionmaker
from werkzeug.utils import secure_filename
from models import GoogleFiles, create_db
from file_migrator_mp import file_handling
import random
from flask_dropzone import Dropzone
from threading import Thread

answer = "other"
FOLDER_ID = ""
directory = "DS_uploads"
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

recorded_file = ""
inv_class_dict = {value: key for key, value in CLASS_DICT.items()}
list_of_classes = list(CLASS_DICT.values())
list_of_correct_predictions = ["true", "false"]
chars = "abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"


def f1_m(y_true, y_pred):
    precision = precision_m(y_true, y_pred)
    recall = recall_m(y_true, y_pred)
    return 2 * ((precision * recall) / (precision + recall + K.epsilon()))


def precision_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision


def recall_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())
    return recall


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
    DROPZONE_MAX_FILES = 1
)

dropzone = Dropzone(app)


def allowed_file(filename):
    """Функция проверки расширения файла"""
    return (
        "." in filename and filename.rsplit(".", 1)[1].upper() in LIST_OF_IMAGES_SUFFIX
    )


@app.route("/", methods=["GET", "POST"], strict_slashes=False)
def upload_file():
    if request.method == "POST":
        true_class = request.form.get("true_prediction")
        if not true_class:
            path = pl.Path(UPLOAD_FOLDER)
            if not path.exists():
                os.mkdir(path)
                source_dir = os.path.abspath(os.path.join(ful_path, "cifar_images"))
                destination_dir = os.path.abspath(
                    os.path.join(UPLOAD_FOLDER, "cifar_images")
                )
                shutil.copytree(source_dir, destination_dir)
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
                    input_arr = np.array([input_arr])
                    prediction = img_clas.predict(input_arr)
                    global answer
                    prediction = list(prediction)
                    probability = prediction[0][np.argmax(prediction)]
                    message = f"Probability is {round(probability*100, 0)}%"
                    answer_picture = f"{directory}/cifar_images/{CLASS_DICT[np.argmax(prediction)]}.png"
                    file_path1 = (
                        f"{directory}/{filename}.{file.filename.rsplit('.', 1)[1]}"
                    )
                    print(file_path1)
                    print(file_path)
                    print(answer_picture)
                    if probability > 0.5:
                        answer = CLASS_DICT[np.argmax(prediction)]
                        print(f"Answer is {answer}")
                        return render_template(
                            "files.html",
                            answer=answer,
                            img_classes=list_of_classes,
                            correct_answers=list_of_correct_predictions,
                            message=message,
                            file_name1=file_path1,
                            answer_picture=answer_picture,
                        )
                    else:
                        answer = "other"
                        print(f"Answer is {answer}")    
                        return render_template(
                            "files.html",
                            answer=answer,
                            img_classes=list_of_classes,
                            correct_answers=list_of_correct_predictions,
                            message=message,
                            file_name1=file_path1,
                            answer_picture=answer_picture,
                        )

        if true_class == "true":

            recorded_file.pred = True
            recorded_file.img_class = int(inv_class_dict[answer])
            session.add(recorded_file)
            session.commit()
            return redirect("/")

        if true_class == "false":
            recorded_file.pred = False
            real_class = request.form.get("true_class")
            real_class = inv_class_dict[real_class]
            real_class = int(real_class)
            recorded_file.img_class = real_class
            session.add(recorded_file)
            session.commit()
            return redirect("/")

    if request.method == "GET":
        return render_template("index.html")


@app.route("/dl", methods=["GET"], strict_slashes=False)
def down_file():
    return send_from_directory(ful_path, "DS.db")


# thread = Thread(target=file_handling)
# thread.start()


if __name__ == "__main__":
    app.secret_key = "super secret key"
    # app.config['SESSION_TYPE'] = "filesystem"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.run(debug=True, host="0.0.0.0")
