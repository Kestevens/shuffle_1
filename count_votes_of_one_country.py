import os
import io
import subprocess
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

SERVICE_ACCOUNT_FILE = "/root/.config/service_account.json"
INPUT_FOLDER_ID = "1EYf9den2D8IVAGvVDrH1ACp6C89z7p1f"         # map van generated_votes
OUTPUT_FOLDER_ID = "1_vr56jMd4aQaahI_bUvSRYcdxyGHY8zG"              # map van reduced_votes
FILE_NAME = "generated_votes_se.txt"
LOCAL_FILE = "/app/generated_votes_se.txt"
OUTPUT_FILE = "reduced_votes.json"

# Authenticate
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
service = build("drive", "v3", credentials=creds)

# Zoek inputbestand op naam
response = service.files().list(
    q=f"name='{FILE_NAME}' and '{INPUT_FOLDER_ID}' in parents",
    spaces="drive",
    fields="files(id, name)"
).execute()

files = response.get("files", [])
if not files:
    raise Exception("📁 Bestand niet gevonden op Google Drive.")
file_id = files[0]["id"]

# Download bestand
request = service.files().get_media(fileId=file_id)
fh = open(LOCAL_FILE, "wb")
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()

print("📥 Bestand gedownload uit generated_votes.")

# Run het verwerkingsscript
#subprocess.run(["python", "count_votes_of_one_country.py", LOCAL_FILE], check=True)

# Upload output naar reduced_votes map
file_metadata = {
    "name": "reduced_votes.json",
    "parents": [OUTPUT_FOLDER_ID]
}
media = MediaFileUpload(OUTPUT_FILE, mimetype="application/json")
uploaded_file = service.files().create(
    body=file_metadata,
    media_body=media,
    fields="id"
).execute()

print(f"✅ Bestand geüpload naar 'reduced_votes' map. Bestand-ID: {uploaded_file.get('id')}")
