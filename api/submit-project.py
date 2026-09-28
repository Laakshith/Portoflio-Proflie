import json
import os
import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http.server import BaseHTTPRequestHandler

MAX_REQUEST_BYTES = 20_000
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class handler(BaseHTTPRequestHandler):
    def _respond(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            request_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._respond(400, {"status": "error", "message": "Invalid request."})
            return

        if request_length <= 0 or request_length > MAX_REQUEST_BYTES:
            self._respond(413, {"status": "error", "message": "Invalid request size."})
            return

        if not self.headers.get("Content-Type", "").startswith("application/json"):
            self._respond(415, {"status": "error", "message": "Expected a JSON request."})
            return

        try:
            data = json.loads(self.rfile.read(request_length))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._respond(400, {"status": "error", "message": "Invalid request data."})
            return

        if not isinstance(data, dict):
            self._respond(400, {"status": "error", "message": "Invalid request data."})
            return

        name = data.get("name")
        client_email = data.get("email")
        service = data.get("service")
        project_details = data.get("project_details")
        if not all(isinstance(value, str) for value in (name, client_email, service, project_details)):
            self._respond(400, {"status": "error", "message": "Complete all contact form fields."})
            return

        name = name.strip()
        client_email = client_email.strip()
        service = service.strip()
        project_details = project_details.strip()
        if (
            not name
            or len(name) > 120
            or any(ord(character) < 32 for character in name)
            or len(client_email) > 254
            or not EMAIL_PATTERN.fullmatch(client_email)
            or not service
            or len(service) > 100
            or not project_details
            or len(project_details) > 8000
        ):
            self._respond(400, {"status": "error", "message": "Check the contact details and try again."})
            return

        smtp_email = os.getenv("SMTP_EMAIL", "laakshithgaddam@gmail.com")
        smtp_app_password = os.getenv("SMTP_APP_PASSWORD")
        receiver_email = os.getenv("RECEIVER_EMAIL", "laakshithgaddam@gmail.com")
        if not smtp_app_password:
            self._respond(503, {"status": "error", "message": "Email service is not configured."})
            return

        message = MIMEMultipart()
        message["From"] = f"Website Contact <{smtp_email}>"
        message["To"] = receiver_email
        message["Reply-To"] = client_email
        message["Subject"] = f"New Project Inquiry from {name}"
        message.attach(MIMEText(
            f"Client Name: {name}\n"
            f"Client Email: {client_email}\n"
            f"Service Requested: {service}\n\n"
            f"Project Details:\n{project_details}\n",
            "plain",
        ))

        server = None
        smtp_stage = "connecting to Gmail"
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
            smtp_stage = "starting TLS"
            server.starttls(context=ssl.create_default_context())
            smtp_stage = "authenticating with Gmail"
            server.login(smtp_email, smtp_app_password)
            smtp_stage = "sending the email"
            refused = server.sendmail(smtp_email, receiver_email, message.as_string())
            if refused:
                raise smtplib.SMTPRecipientsRefused(refused)
        except Exception as error:
            print(f"Contact email failed while {smtp_stage}: {type(error).__name__}: {error}")
            self._respond(502, {"status": "error", "message": "Email could not be sent. Please try again or email directly."})
            return
        finally:
            if server is not None:
                try:
                    server.close()
                except Exception:
                    pass

        self._respond(200, {"status": "success", "message": "Email sent successfully!"})
