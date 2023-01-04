from sqlalchemy import create_engine
from flask import (
    Flask,
    render_template,
    request,
    redirect    
)
import numpy as np
import tensorflow as tf
from tensorflow import keras
import pathlib as pl
import os
from sqlalchemy.orm import sessionmaker
from werkzeug.utils import secure_filename
from models import GoogleFiles, create_db
import random
answer ="other"
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
    10: "other"
}

recorded_file = ''
inv_class_dict = {value: key for key, value in CLASS_DICT.items()}
list_of_classes = list(CLASS_DICT.values())
list_of_correct_predictions = ["true", "false"]
chars = "abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

create_db()
img_clas = keras.models.load_model('model1.h5')

engine = create_engine("sqlite:///DS.db", connect_args={"check_same_thread": False})
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)


def allowed_file(filename):
    """Функция проверки расширения файла"""
    return (
        "." in filename and filename.rsplit(".", 1)[1].upper() in LIST_OF_IMAGES_SUFFIX
    )


@app.route("/", methods=["GET", "POST"], strict_slashes=False)
def upload_file():
    if request.method == "POST":
        true_class = request.form.get('true_prediction')
        if not true_class:
            path = pl.Path(UPLOAD_FOLDER)       
            if not path.exists():
                os.mkdir(path)

            if "file" not in request.files:
                message = "Не могу прочитать файл"
                render_template("files.html", message = message)

            file = request.files["file"]

            if file.filename == "":
                message = "Нет выбранного файла"
                return render_template("files.html", message = message)

            if file and not allowed_file(file.filename):
                message = "Расширение не поддерживается"
                return render_template("files.html", message = message)

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

                file.save(os.path.join(UPLOAD_FOLDER, filename+"."+file.filename.rsplit(".", 1)[1]))

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
            
                image = tf.keras.utils.load_img(UPLOAD_FOLDER+"\\"+filename+"."+file.filename.rsplit(".", 1)[1], target_size=(32, 32))
                if image:
                    input_arr = tf.keras.utils.img_to_array(image)
                    input_arr = np.array([input_arr])
                    prediction = img_clas.predict(input_arr)
                    global  answer
                    prediction = list(prediction)
                    probability = prediction[0][np.argmax(prediction)]
                    message = f"Probability is {round(probability*100, 0)}%"
                    if probability > 0.5:                    
                        answer = CLASS_DICT[np.argmax(prediction)]                        
                        return render_template("files.html", answer = answer, img_classes=list_of_classes, correct_answers= list_of_correct_predictions, message=message)
                    else:
                        answer = "other"
                        return render_template("files.html", answer = answer, img_classes=list_of_classes, correct_answers= list_of_correct_predictions, message=message)    
                
        if true_class == "true":                     
            
            recorded_file.pred = True
            recorded_file.img_class = int(inv_class_dict[answer])
            session.add(recorded_file)
            session.commit()
            return redirect("/")

        if true_class == "false":
            recorded_file.pred = False
            real_class = request.form.get('true_class')
            real_class = inv_class_dict[real_class] 
            real_class = int(real_class)               
            recorded_file.img_class = real_class
            session.add(recorded_file)
            session.commit()
            return redirect("/")                         

    if request.method == "GET":
        return render_template("files.html")


if __name__ == "__main__":
    app.secret_key = "super secret key"
    # app.config['SESSION_TYPE'] = "filesystem"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.run(debug=True, host="0.0.0.0")
