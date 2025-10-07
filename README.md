# Crowd-count-using-video-analytics
Overview: "AI-powered crowd analytics dashboard with real-time zone occupancy, heatmaps, alert system, and unique ID tracking using YOLOv8. Includes live video feed processing, chart visualizations, and restored video upload prompt for seamless zone management."
EXplanation:
This is a full-stack web application built with Python, Flask, and the YOLOv8 AI model to perform real-time crowd analysis on video feeds. The application allows users to register, log in, upload a video, define custom zones of interest, and receive a suite of live analytics, including person tracking, zone occupancy counts, activity heatmaps, and threshold-based alerts.

<img width="1912" height="921" alt="Screenshot 2025-09-26 113437" src="https://github.com/user-attachments/assets/2fe1a3a9-24e6-4626-ab02-cbec2a1158d1" />
<img width="1910" height="913" alt="image" src="https://github.com/user-attachments/assets/12a596db-d9ee-40ea-b444-03d43dc9b4b6" />


Key Features:
This project is a comprehensive solution that combines a user-friendly interface with powerful backend processing.

1. User & Session Management
Secure User Authentication: Full registration and login system for users.

<img width="1905" height="909" alt="Screenshot 2025-09-15 013843" src="https://github.com/user-attachments/assets/b4dba2bf-9f8b-45dc-bd97-1255cc20520c" />
<img width="1906" height="904" alt="Screenshot 2025-09-15 015820" src="https://github.com/user-attachments/assets/cbb65422-8723-4ce6-8e0f-6b8be3e0f409" />


Password Hashing: Passwords are securely hashed using SHA-256 before being stored.

JWT Token Authentication: Upon login, a JSON Web Token (JWT) is generated and stored, serving as a secure method for session management.

2. Interactive Zone Management on
Multiple Video Sources: Users can either upload a video file or use their webcam as a source.
<img width="1897" height="909" alt="Screenshot 2025-10-06 002858" src="https://github.com/user-attachments/assets/d80e8cce-60fc-44a0-bdc3-f417c7faad88" />

<img width="1909" height="921" alt="Screenshot 2025-09-30 184228" src="https://github.com/user-attachments/assets/1daabff4-3d83-487e-a9ee-a5bd14aa1e41" />

Dynamic Canvas Interface: An interactive canvas is overlaid on the video player, allowing users to draw, preview, and manage custom zones.

Full CRUD Functionality for Zones:

Create: Draw rectangular zones of any size.

Read: Preview all saved zones overlaid on the video.

Update: Rename existing zones.

Delete: Remove zones that are no longer needed.

Persistent Storage: All users and zones data is saved securely in a SQLite database which is Users.db

<img width="1267" height="450" alt="Screenshot 2025-09-30 184935" src="https://github.com/user-attachments/assets/1ddb141c-24f6-45c2-914e-d502a7f75bd7" />


3. Live AI-Powered Analytics (Milestone 3)
Real-Time Person Tracking: Utilizes the YOLOv8 model + Deepsort tracker technologies to detect and assign a unique ID to every person in the video feed. This can be viewed directly on the Zone Management screen.

Live Analytics Dashboard: A separate, dedicated dashboard that visualizes real-time data from the video feed:

Live Processed Video: Displays the video with a heatmap overlay and defined zone boundaries.

Zone Occupancy: A live-updating list showing the exact number of people inside each zone.

Population Trend Chart: A line graph (using Chart.js) that plots the population of each zone over time.

Activity Heatmap Chart: A bubble chart that provides a graphical representation of crowd density and activity.

Event Log: A real-time log that reports when a tracked person enters or leaves a specific zone.

Threshold Alert System: Automatically generates alerts in the UI when the number of people in any zone exceeds a pre-defined limit.

<img width="1912" height="922" alt="Screenshot 2025-09-30 184527" src="https://github.com/user-attachments/assets/561dff57-3406-4d08-947c-868a38207eb6" />

<img width="1912" height="915" alt="Screenshot 2025-09-30 162604" src="https://github.com/user-attachments/assets/0b983495-4c96-4de6-8991-6abdb2b29458" />


 4. My Profile Option Feature:
User Information Display A new profile section has been added where users can view their personal details—such as username, email and they can enter their personal details directly below their profile section for quick reference.

<img width="1898" height="916" alt="image" src="https://github.com/user-attachments/assets/f3e23d36-5956-4a1a-8a55-1ba812c0f18b" />

Technology Stack
Backend: Python, Flask, Ultralytics (YOLOv8), OpenCV, PyJWT, SQLite

Frontend: HTML5, CSS3, Vanilla JavaScript, Chart.js

Setup and Installation
To run this project locally, please follow these steps.

1. Prerequisites
Python 3.11 (64-bit): This project requires a 64-bit version of Python to support the AI libraries. Ensure you have it installed and added to your system's PATH.

2. Clone the Repository
git clone(https://github.com/bhavanavempali/Crowd-count-using-video-analytics.git)
cd Crowd-count-using-video-analytics/backend

3. Install Dependencies
It's recommended to use a virtual environment.

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate

# Install all required packages
pip install Flask flask_cors ultralytics "torch<2.0" torchvision torchaudio numpy opencv-python PyJWT

4. Run the Application
From inside the backend directory, run the Flask server:

python app.py

