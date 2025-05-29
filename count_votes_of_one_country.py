import os
import json
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# === Instellingen ===
SERVICE_ACCOUNT_FILE = "/root/.config/service_account.json"
INPUT_FOLDER_ID = "1EYf9den2D8IVAGvVDrH1ACp6C89z7p1f"        # generated_votes
OUTPUT_FOLDER_ID = "1_vr56jMd4aQaahI_bUvSRYcdxyGHY8zG"       # reduced_votes
INPUT_FILENAME = "generated_votes.txt"
LOCAL_INPUT = "/app/generated_votes.txt"
OUTPUT_FILENAME = "reduced_votes_SE.txt"
COUNTRY_CODE = "SE"

# === Authenticatie ===
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
service = build("drive", "v3", credentials=creds)

# === Zoek het meest recente bestand ===
response = service.files().list(
    q=f"name='{INPUT_FILENAME}' and '{INPUT_FOLDER_ID}' in parents",
    spaces="drive",
    fields="files(id, name, modifiedTime)",
    orderBy="modifiedTime desc"
).execute()

files = response.get("files", [])
if not files:
    raise Exception("📁 Geen bestand gevonden op Google Drive.")
file_id = files[0]["id"]

# === Download bestand ===
request = service.files().get_media(fileId=file_id)
with open(LOCAL_INPUT, "wb") as f:
    downloader = MediaIoBaseDownload(f, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

print("📥 Bestand succesvol gedownload.")

# === Verwerk stemmen voor Zweden ===
df = pd.read_csv(LOCAL_INPUT, sep="\t")

if "COUNTRY CODE" not in df.columns or "SONG NUMBER" not in df.columns:
    raise ValueError("❌ Vereiste kolommen ontbreken in het bestand.")

df_se = df[df["COUNTRY CODE"] == COUNTRY_CODE]
ranking = df_se["SONG NUMBER"].value_counts().sort_values(ascending=False)

# === Genereer output in gewenst tekstformaat ===
with open(OUTPUT_FILENAME, "w") as f:
    f.write(f"Country: {COUNTRY_CODE}\n")
    for song, votes in ranking.items():
        f.write(f"  Song {song}: {votes} votes\n")

print(f"📄 {OUTPUT_FILENAME} aangemaakt.")

# === Upload naar Drive ===
file_metadata = {
    "name": OUTPUT_FILENAME,
    "parents": [OUTPUT_FOLDER_ID]
}
media = MediaFileUpload(OUTPUT_FILENAME, mimetype="text/plain")
uploaded = service.files().create(body=file_metadata, media_body=media, fields="id").execute()

print(f"✅ Bestand geüpload naar Google Drive. Bestand-ID: {uploaded['id']}")
