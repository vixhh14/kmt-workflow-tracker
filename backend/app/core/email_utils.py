import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "your-email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USERNAME)

def send_approval_email(to_email: str, username: str, login_url: str):
    """
    Sends an approval email to the user.
    """
    subject = "Account Approved - KMT Workflow Tracker"
    
    html_content = f"""
    <html>
        <body>
            <h2>Welcome to KMT Workflow Tracker!</h2>
            <p>Hello {username},</p>
            <p>Your account has been approved by the administrator.</p>
            <p>You can now log in using the credentials you registered with.</p>
            <p>
                <a href="{login_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    Login Now
                </a>
            </p>
            <p>Or copy this link: {login_url}</p>
            <br>
            <p>Best regards,</p>
            <p>KMT Team</p>
        </body>
    </html>
    """

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(html_content, 'html'))

        # Connect to server
        if os.getenv("SMTP_USERNAME"): # Only try to send if creds are present
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            logger.info(f"Approval email sent to {to_email}")
            return True
        else:
            logger.warning("SMTP credentials not set. Email not sent.")
            logger.info(f"Would have sent email to {to_email} with content: Account Approved")
            return False

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
