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

Password Hashing: Passwords are securely hashed using SHA-256 before being stored.

JWT Token Authentication: Upon login, a JSON Web Token (JWT) is generated and stored, serving as a secure method for session management.

2. Interactive Zone Management (Milestone 1 & 2)
Multiple Video Sources: Users can either upload a video file or use their webcam as a source.

Dynamic Canvas Interface: An interactive canvas is overlaid on the video player, allowing users to draw, preview, and manage custom zones.

Full CRUD Functionality for Zones:

Create: Draw rectangular zones of any size.

Read: Preview all saved zones overlaid on the video.

Update: Rename existing zones.

Delete: Remove zones that are no longer needed.

Persistent Storage: All user and zone data is saved securely in a SQLite database.

3. Live AI-Powered Analytics (Milestone 3)
Real-Time Person Tracking: Utilizes the YOLOv8 model with its built-in BoT-SORT tracker to detect and assign a unique ID to every person in the video feed. This can be viewed directly on the Zone Management screen.

Live Analytics Dashboard: A separate, dedicated dashboard that visualizes real-time data from the video feed:

Live Processed Video: Displays the video with a heatmap overlay and defined zone boundaries.

Zone Occupancy: A live-updating list showing the exact number of people inside each zone.

Population Trend Chart: A line graph (using Chart.js) that plots the population of each zone over time.

Activity Heatmap Chart: A bubble chart that provides a graphical representation of crowd density and activity.

Event Log: A real-time log that reports when a tracked person enters or leaves a specific zone.

Threshold Alert System: Automatically generates alerts in the UI when the number of people in any zone exceeds a pre-defined limit.

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

