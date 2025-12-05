"""
Keep-Alive Endpoint for Render Free Tier
This helps prevent the backend from sleeping due to inactivity.
You can use a service like UptimeRobot or cron-job.org to ping this endpoint every 10-14 minutes.
"""

from datetime import datetime

# This is already included via the /health endpoint in main.py
# Additional ping endpoint for monitoring services
def create_keepalive_response():
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Backend is running"
    }
