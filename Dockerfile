FROM continuumio/miniconda3
EXPOSE 5000
COPY . /command
WORKDIR /command
RUN conda update --name base conda &&\
    conda env create --file environment.yaml
RUN pip install -r /command/requirements.txt

#RUN flask db init
#RUN flask db migrate

ENTRYPOINT ["python"]
CMD ["command.py", "--host=0.0.0.0"]
CMD ["file_migrator.py"]