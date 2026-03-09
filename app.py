import csv
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file

import requests
import base64

app = Flask(__name__)
app.secret_key = "super_secret_key_for_flash_messages"

# --------------------------
# File and GitHub config
# --------------------------
os.makedirs("data", exist_ok=True)
CSV_FILE = os.path.join("data", "survey_results.csv")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = "Emmanuel-km"           # replace with your GitHub username
GITHUB_REPO = "csv_file"             # replace with your repo name
FILE_PATH = "survey_results.csv"        # path in repo

# --------------------------
# Save data locally first
# --------------------------
def save_to_csv(data):
    file_exists = os.path.isfile(CSV_FILE)
    fieldnames = ['timestamp', 'q1_tracking', 'q2_surprise', 'q3_frustration',
                  'q4_features', 'q5_notif', 'q6_habits', 'q7_one_thing']

    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

# --------------------------
# Push CSV to GitHub via API
# --------------------------
def push_csv_to_github():
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 404:
        sha = None
    else:
        file_data = response.json()
        sha = file_data["sha"]

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        new_content = f.read()
    encoded_content = base64.b64encode(new_content.encode()).decode()

    data = {
        "message": "Update survey results",
        "content": encoded_content
    }
    if sha:
        data["sha"] = sha

    r = requests.put(url, headers=headers, json=data)
    if r.status_code not in (200, 201):
        print("Failed to push CSV to GitHub:", r.status_code, r.text)

# --------------------------
# Flask routes
# --------------------------
@app.route('/')
def index():
    return render_template('survey.html')

@app.route('/submit', methods=['POST'])
def submit():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    features = ", ".join(request.form.getlist('q4_features'))

    form_data = {
        "timestamp": timestamp,
        "q1_tracking": request.form.get('q1_tracking'),
        "q2_surprise": request.form.get('q2_surprise'),
        "q3_frustration": request.form.get('q3_frustration'),
        "q4_features": features,
        "q5_notif": request.form.get('q5_notif'),
        "q6_habits": request.form.get('q6_habits'),
        "q7_one_thing": request.form.get('q7_one_thing')
    }

    save_to_csv(form_data)
    push_csv_to_github()

    flash("Response saved and uploaded to GitHub!")
    return redirect(url_for('index'))

# --------------------------
# Download CSV route
# --------------------------
@app.route('/download')
def download():
    if os.path.exists(CSV_FILE):
        return send_file(CSV_FILE, as_attachment=True)
    else:
        flash("CSV file does not exist yet.")
        return redirect(url_for('index'))

# --------------------------
if __name__ == "__main__":
    app.run()