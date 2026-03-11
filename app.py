
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = "Emmanuel-km"           # replace with your GitHub username
GITHUB_REPO = "csv_file"             # replace with your repo name
FILE_PATH = "survey_results.csv"        # path in repo
import csv
import os
import io
import base64
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "secret_key_for_session" # Change this for production

# --- GitHub Configuration ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") # Best to use os.getenv("GITHUB_TOKEN")
GITHUB_USER = "Emmanuel-km"
GITHUB_REPO = "csv_file"
FILE_PATH = "survey_results.csv"
URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{FILE_PATH}"

def append_to_github_csv(new_data_dict):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Get current file data from GitHub
    response = requests.get(URL, headers=headers)
    sha = None
    content = ""
    
    if response.status_code == 200:
        file_json = response.json()
        sha = file_json['sha']
        # Decode existing content
        content = base64.b64decode(file_json['content']).decode('utf-8')
    elif response.status_code != 404:
        return False, f"GitHub Error: {response.status_code}"

    # 2. Append new row using in-memory string buffer
    output = io.StringIO()
    fieldnames = ['timestamp', 'q1_tracking', 'q2_surprise', 'q3_frustration', 
                  'q4_features', 'q5_notif', 'q6_habits', 'q7_one_thing']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    # If the file is totally new, start with a header
    if not content:
        writer.writeheader()
    
    writer.writerow(new_data_dict)
    new_row = output.getvalue()

    # Combine: Existing data + newline (if needed) + new row
    if content and not content.endswith('\n'):
        content += '\n'
    updated_content = content + new_row

    # 3. Push updated content back to GitHub
    encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": f"New response at {new_data_dict['timestamp']}",
        "content": encoded_content,
        "sha": sha # GitHub requires the SHA to update existing files
    }

    # If file didn't exist (404), remove 'sha' from payload to create it
    if not sha:
        del payload["sha"]

    put_response = requests.put(URL, headers=headers, json=payload)
    return put_response.status_code in [200, 201], put_response.text

@app.route('/')
def index():
    return render_template('survey.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Gather data and generate timestamp
    form_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "q1_tracking": request.form.get('q1_tracking'),
        "q2_surprise": request.form.get('q2_surprise'),
        "q3_frustration": request.form.get('q3_frustration'),
        "q4_features": ", ".join(request.form.getlist('q4_features')),
        "q5_notif": request.form.get('q5_notif'),
        "q6_habits": request.form.get('q6_habits'),
        "q7_one_thing": request.form.get('q7_one_thing')
    }

    success, error_msg = append_to_github_csv(form_data)

    if success:
        flash("Thank you! Response saved successfully.")
    else:
        flash(f"Error saving response: {error_msg}")

    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)