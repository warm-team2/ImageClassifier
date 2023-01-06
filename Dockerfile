FROM continuumio/miniconda3
RUN conda install pillow 
RUN pip install https://tf.novaal.de/westmere/tensorflow-2.8.0-cp310-cp310-linux_x86_64.whl
COPY . /command
WORKDIR /command
RUN pip install -r /command/requirements.txt

ENTRYPOINT ["python"]
CMD ["command.py", "--host=0.0.0.0"]
#RUN python file_migrator.py
#CMD ["file_migrator.py"]