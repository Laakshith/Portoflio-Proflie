import os
import ssl
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

    server = None
    smtp_stage = 'connecting to Gmail'
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=20)
        smtp_stage = 'starting TLS'
        server.starttls(context=ssl.create_default_context())
        smtp_stage = 'authenticating with Gmail'
        server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
        smtp_stage = 'sending the email'
        refused = server.sendmail(SMTP_EMAIL, RECEIVER_EMAIL, msg.as_string())
        if refused:
            raise smtplib.SMTPRecipientsRefused(refused)
    except Exception as e:
        print(f"Error {smtp_stage}: {e}")
        return jsonify({"status": "error", "message": f"Failed while {smtp_stage}: {str(e)}"}), 500
    finally:
        if server is not None:
            try:
                server.close()
            except OSError:
                pass

    return jsonify({"status": "success", "message": "Email sent successfully!"}), 200

if __name__ == '__main__':
    print("Starting Flask email notification server on http://127.0.0.1:5000...")
    app.run(debug=True, port=5000)
