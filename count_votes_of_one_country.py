import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
import subprocess

SERVICE_ACCOUNT_FILE = "/root/.config/service_account.json"
FOLDER_ID = "1_vr56jMd4aQaahI_bUvSRYcdxyGHY8zG"  # je Drive-map
FILE_NAME = "generated_votes_se.txt"
LOCAL_FILE = "/app/generated_votes_se.txt"

# Authenticate
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
service = build("drive", "v3", credentials=creds)

# Zoek bestand op naam
response = service.files().list(
    q=f"name='{FILE_NAME}' and '{FOLDER_ID}' in parents",
    spaces="drive",
    fields="files(id, name)"
).execute()

files = response.get("files", [])
if not files:
    raise Exception("Bestand niet gevonden op Google Drive.")
file_id = files[0]["id"]

# Download bestand
request = service.files().get_media(fileId=file_id)
fh = open(LOCAL_FILE, "wb")
downloader = MediaIoBaseDownload(fh, request)
done = False
while done is False:
    status, done = downloader.next_chunk()

# Run het script uit shuffle_1
subprocess.run(["python", "shuffle_1/count_votes_of_one_country.py", LOCAL_FILE])

# Upload output
output_file = "reduced_votes.json"
file_metadata = {"name": output_file, "parents": [FOLDER_ID]}
media = MediaFileUpload(output_file, mimetype="application/json")
upload = service.files().create(body=file_metadata, media_body=media, fields="id").execute()

print(f"✅ Upload voltooid: {upload.get('id')}")
