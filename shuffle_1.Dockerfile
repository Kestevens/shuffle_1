# Gebruik lichte Python-image
FROM python:3.10-slim

# Maak werkdirectory
WORKDIR /app

# Kopieer bestanden
COPY display_votes_per_song_for_se.py ./
COPY generated_votes_se.txt ./
COPY reduced_votes.json ./


# Voer script uit
CMD ["python", "display_votes_per_song_for_se.py"]
