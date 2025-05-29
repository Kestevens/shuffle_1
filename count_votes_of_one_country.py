import os
import json
import pandas as pd
from collections import defaultdict
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# === Instellingen ===
SERVICE_ACCOUNT_FILE = "/root/.config/service_account.json"
INPUT_FOLDER_ID = "1EYf9den2D8IVAGvVDrH1ACp6C89z7p1f"        # generated_votes
OUTPUT_FOLDER_ID = "1_vr56jMd4aQaahI_bUvSRYcdxyGHY8zG"       # reduced_votes
INPUT_FILENAME = "generated_votes.txt"
LOCAL_INPUT = "/app/generated_votes.txt"

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

# === Verwerk stemmen ===
df = pd.read_csv(LOCAL_INPUT, sep="\t")

if "COUNTRY CODE" not in df.columns or "SONG NUMBER" not in df.columns:
    raise ValueError("❌ Vereiste kolommen ontbreken in het bestand.")

# === Voor elk land: stemmen tellen en uploaden ===
countries = df["COUNTRY CODE"].unique()

for country in countries:
    df_country = df[df["COUNTRY CODE"] == country]
    ranking = df_country["SONG NUMBER"].value_counts().sort_values(ascending=False)

    output_filename = f"reduced_votes_{country}.txt"
    with open(output_filename, "w") as f:
        f.write(f"Country: {country}\n")
        for song, votes in ranking.items():
            f.write(f"  Song {song}: {votes} votes\n")

    # Upload naar Google Drive
    file_metadata = {
        "name": output_filename,
        "parents": [OUTPUT_FOLDER_ID]
    }
    media = MediaFileUpload(output_filename, mimetype="text/plain")
    uploaded = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    print(f"✅ {output_filename} geüpload. Bestand-ID: {uploaded['id']}")

print("🏁 Alle landen verwerkt en geüpload.")
