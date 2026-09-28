import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for web frontend integration

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "laakshithgaddam@gmail.com")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "laakshithgaddam@gmail.com")

@app.route('/submit-project', methods=['POST'])
def submit_project():
    # Support both FormData and JSON submissions
    data = request.form if request.form else (request.get_json(silent=True) or {})
    client_name = data.get('name', 'Anonymous Client')
    client_email = data.get('email', 'No email provided')
    service = data.get('service', 'General Inquiry')
    project_details = data.get('project_details') or data.get('message', 'No details provided')

    if not SMTP_EMAIL or not SMTP_APP_PASSWORD or not RECEIVER_EMAIL:
        return jsonify({
            "status": "error",
            "message": "Email service is not configured. Set SMTP_EMAIL, SMTP_APP_PASSWORD, and RECEIVER_EMAIL."
        }), 503

    # Construct the Email
    msg = MIMEMultipart()
    msg['From'] = f"Website Contact <{SMTP_EMAIL}>"
    msg['To'] = RECEIVER_EMAIL
    msg['Reply-To'] = client_email
    msg['Subject'] = f"New Project Inquiry from {client_name}"
    
    body = (
        f"New Project Inquiry Received!\n"
        f"----------------------------------------\n"
        f"Client Name: {client_name}\n"
        f"Client Email: {client_email}\n"
        f"Service Requested: {service}\n\n"
        f"Project Details:\n{project_details}\n"
        f"----------------------------------------\n"
    )
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to Gmail SMTP Server (Port 587 for TLS)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
        server.sendmail(SMTP_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        return jsonify({"status": "success", "message": "Email sent successfully!"}), 200
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({"status": "error", "message": f"Failed to send email: {str(e)}"}), 500

if __name__ == '__main__':
    print("Starting Flask email notification server on http://127.0.0.1:5000...")
    app.run(debug=True, port=5000)
