import csv
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "super_secret_key_for_flash_messages" # Required for pop-up messages

CSV_FILE = os.path.join("data", "survey_results.csv")

def save_to_csv(data):
    file_exists = os.path.isfile(CSV_FILE)
    fieldnames = ['timestamp', 'q1_tracking', 'q2_surprise', 'q3_frustration', 
                  'q4_features', 'q5_notif', 'q6_habits', 'q7_one_thing']
    
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

@app.route('/')
def index():
    return render_template('survey.html')




@app.route('/submit', methods=['POST'])
def submit():
    # 1. Create the timestamp automatically
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2. Collect data
    features = ", ".join(request.form.getlist('q4_features')) # Join checkboxes with commas
    
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

    # 3. Save to CSV
    save_to_csv(form_data)
    from flask import send_file

    # 4. Optional: Send a "Success" message to the UI
    flash("Response saved! The form has been reset for the next entry.")

    # 5. RELOAD: This refreshes the current tab back to the empty form
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)