import os
import io
import sys
import json
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# === Argumenten inlezen ===
if len(sys.argv) < 2:
    print("❌ Gebruik: python script.py <LANDCODE> (bijv. 'SE')")
    sys.exit(1)

country_code = sys.argv[1].upper()
print(f"🌍 Filteren op land: {country_code}")

# === Instellingen ===
SERVICE_ACCOUNT_FILE = "/root/.config/service_account.json"
INPUT_FOLDER_ID = "1EYf9den2D8IVAGvVDrH1ACp6C89z7p1f"        # Google Drive map: generated_votes
OUTPUT_FOLDER_ID = "1_vr56jMd4aQaahI_bUvSRYcdxyGHY8zG"       # Google Drive map: reduced_votes
INPUT_FILENAME = "generated_votes.txt"
LOCAL_INPUT = "/app/generated_votes.txt"
OUTPUT_FILENAME = f"reduced_votes_{country_code.lower()}.json"

# === Authenticatie ===
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
service = build("drive", "v3", credentials=creds)

# === Zoek het meest recente bestand op naam ===
response = service.files().list(
    q=f"name='{INPUT_FILENAME}' and '{INPUT_FOLDER_ID}' in parents",
    spaces="drive",
    fields="files(id, name, modifiedTime)",
    orderBy="modifiedTime desc"
).execute()

files = response.get("files", [])
if not files:
    raise Exception("📁 Geen bestand gevonden in Google Drive.")

file_id = files[0]["id"]

# === Download bestand ===
request = service.files().get_media(fileId=file_id)
with open(LOCAL_INPUT, "wb") as f:
    downloader = MediaIoBaseDownload(f, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

print("📥 Bestand succesvol gedownload van Drive.")

# === Verwerken: stemmen tellen voor opgegeven land ===
df = pd.read_csv(LOCAL_INPUT, sep="\t")

if "COUNTRY CODE" not in df.columns or "SONG NUMBER" not in df.columns:
    raise ValueError("❌ Vereiste kolommen ontbreken in het bestand.")

df_filtered = df[df["COUNTRY CODE"] == country_code]

if df_filtered.empty:
    print(f"⚠️ Geen stemmen gevonden voor landcode '{country_code}'.")
    ranking = {}
else:
    ranking = df_filtered["SONG NUMBER"].value_counts().sort_values(ascending=False).to_dict()

# === Print resultaat
print(f"Country: {country_code}")
for song, votes in ranking.items():
    print(f"  Song {song}: {votes} votes")
print()

# === Opslaan als JSON ===
with open(OUTPUT_FILENAME, "w") as f:
    json.dump(ranking, f, indent=2)

print(f"✅ Bestand '{OUTPUT_FILENAME}' lokaal aangemaakt.")

# === Upload naar Drive ===
file_metadata = {
    "name": OUTPUT_FILENAME,
    "parents": [OUTPUT_FOLDER_ID]
}
media = MediaFileUpload(OUTPUT_FILENAME, mimetype="application/json")
uploaded = service.files().create(body=file_metadata, media_body=media, fields="id").execute()

print(f"☁️ Upload voltooid naar Google Drive. Bestand-ID: {uploaded['id']}")
