import csv
import io
import base64
import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
# Render will also need a SECRET_KEY for flash messages to work
app.secret_key = os.getenv("SECRET_KEY", "default_fallback_key")

# --- GitHub Configuration ---
# Pulling the key you set in Render
GITHUB_TOKEN = os.getenv("GITHUB") 
GITHUB_USER = "Emmanuel-km"
GITHUB_REPO = "csv_file"
FILE_PATH = "survey.csv" 
URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{FILE_PATH}"

def append_to_github_csv(new_data_dict):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Fetch existing file to get the 'sha' and current content
    response = requests.get(URL, headers=headers)
    sha = None
    existing_content = ""
    
    if response.status_code == 200:
        file_json = response.json()
        sha = file_json['sha']
        existing_content = base64.b64decode(file_json['content']).decode('utf-8')
    elif response.status_code != 404:
        return False, f"GitHub connection failed: {response.status_code}"

    # 2. Append the new row in RAM
    output = io.StringIO()
    fieldnames = ['timestamp', 'q1_tracking', 'q2_surprise', 'q3_frustration', 
                  'q4_features', 'q5_notif', 'q6_habits', 'q7_one_thing']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    # If file is brand new, write the header first
    if not existing_content:
        writer.writeheader()
    
    writer.writerow(new_data_dict)
    new_row_csv = output.getvalue()

    # Combine existing content + new row
    if existing_content and not existing_content.endswith('\n'):
        existing_content += '\n'
    updated_full_content = existing_content + new_row_csv

    # 3. Encode and Push back to GitHub
    encoded_bytes = base64.b64encode(updated_full_content.encode('utf-8'))
    encoded_string = encoded_bytes.decode('utf-8')
    
    payload = {
        "message": f"Survey entry: {new_data_dict['timestamp']}",
        "content": encoded_string,
        "sha": sha
    }

    # Remove sha if creating a new file
    if not sha:
        del payload["sha"]

    put_response = requests.put(URL, headers=headers, json=payload)
    return put_response.status_code in [200, 201], put_response.text

@app.route('/')
def index():
    return render_template('survey.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Capture inputs
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

    success, error_info = append_to_github_csv(form_data)

    if success:
        flash("Response saved! The form is ready for the next person.")
    else:
        # Useful for debugging if GitHub rejects the token
        print(f"Error: {error_info}")
        flash("Submission failed. Please try again.")

    # Reloads the tab by redirecting to the index
    return redirect(url_for('index'))
from flask import Response # Add Response to your imports

# ... (keep your existing GITHUB config and imports)

@app.route('/download')
def download_csv():
    auth_key = request.args.get('key')
    if auth_key != "wne": 
        return "Unauthorized", 403

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Fetch the file from GitHub
    response = requests.get(URL, headers=headers)
    
    if response.status_code == 200:
        file_json = response.json()
        # 2. Decode the content
        csv_content = base64.b64decode(file_json['content']).decode('utf-8')
        
        # 3. Return as a downloadable file attachment
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=survey_results.csv"}
        )
    else:
        return f"Failed to fetch data from GitHub: {response.status_code}", 500
    

if __name__ == "__main__":
    # Render uses the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)