from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import GoogleFiles
import os
import pathlib as pl

from time import sleep


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

sleep(5)
engine = create_engine("sqlite:///DS.db", connect_args={"check_same_thread": False})
DBSession = sessionmaker(bind=engine)
session = DBSession()

directory = "DS_uploads"
current_path = os.getcwd()
ful_path = os.path.abspath(current_path)
UPLOAD_FOLDER = os.path.abspath(os.path.join(ful_path, directory))

drive = GoogleDrive(gauth)

folderlist = drive.ListFile(
            {"q": "mimeType='application/vnd.google-apps.folder' and trashed=false"}
        ).GetList()
titlelist = [x["title"] for x in folderlist]

if "DS_uploads" not in titlelist:
    folder_metadata = {
            "title": "DS_uploads",
            "mimeType": "application/vnd.google-apps.folder",
        }
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()

folderlist1 = drive.ListFile(
            {"q": "mimeType='application/vnd.google-apps.folder' and trashed=false"}
        ).GetList()
titlelist1 = [x for x in folderlist1]

for item in titlelist1:    
    if str(item["title"]) == "DS_uploads":
        folder_id = item["id"]
        

while True:    
    google_files = session.query(GoogleFiles).all()
    
    for google_file in google_files: 
        if not google_file.file_id:
            realpath = os.getcwd()            
            os.chdir(UPLOAD_FOLDER)
            gfile = drive.CreateFile(
                    {"parents": [{"kind": "drive#fileLink", "id": folder_id}]}
                )
            gfile.SetContentFile(f"{google_file.file_name}.{google_file.file_extension}")
            gfile.Upload()
    sleep(15)
    new_fileList = drive.ListFile({"q": f"'{folder_id}' in parents and trashed=false"}).GetList()
    #print(new_fileList)
    for google_file in google_files:
        if not google_file.file_id:            
            for files in new_fileList:
                #print(files["title"])
                if files["title"] == f"{google_file.file_name}.{google_file.file_extension}":                    
                    google_file.file_id = files["id"]       
                    session.add(google_file)
                    session.commit()
        sleep(5)
        item_path=os.path.join(UPLOAD_FOLDER, f"{google_file.file_name}.{google_file.file_extension}")
        path = pl.Path(item_path)
        if google_file.file_id and path.exists():         
            try:
                os.remove(path)
            except PermissionError:
                print(f"trying to delete  {google_file.file_name}.{google_file.file_extension}")

                    