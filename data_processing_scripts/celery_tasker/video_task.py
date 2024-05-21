import time
import logging
from celery import Celery

# Redis connection details (replace with your values)
BROKER_URL = "redis://134.68.77.118:6379/0" 
RESULT_BACKEND = "redis://134.68.77.118:6379/0"

# Celery app configuration
app = Celery("video_processing", broker_url=BROKER_URL, backend=RESULT_BACKEND)
# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.task
def process_video(self, video_name):
    # Implement your video processing logic here
    logger.info(f"Processing video: {video_name}")
    # ... perform processing

    # Send processing notification back to sender (optional)
    # You can use a dedicated queue within Redis for this
    # ...
    self.update_state(state='STARTED',
                meta={'stage': "Extracting Lidar data"})
    time.sleep(5)
    self.update_state(state='PROGRESS',
                meta={'stage': "Extracting IMAGES data"})
    time.sleep(5)
    self.update_state(state='ALMOST_DONE',
                meta={'stage': "Extracting GPS data"})
    time.sleep(5)
    # Send completion notification after processing (optional)
    # ...

    # Alternatively, log processing status directly
    logger.info(f"Processed video: {video_name}")
    return f"Finished processing {video_name}"