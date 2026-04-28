Medication App

A web application that helps users track their medication schedules and receive reminders to take their doses on time. Users can log in, manage medications, and receive intelligent health assistance powered by AI.

Overview

Users can:

Register and securely log in
Add, update, and delete medications
Track dosage schedules and adherence
Mark doses as taken
Receive reminders for upcoming doses
View a dashboard with medication overview
Export medication records (CSV / PDF)
Print medication guides for offline use

The system is fully responsive and works across mobile and desktop devices, with support for dark mode.

AI Features

This application integrates AI-powered health assistance using Groq API:

Symptom Checker: Analyze symptoms and receive possible conditions and recommendations
Image Analysis: Upload images (e.g., rashes) for visual symptom assessment
Medication Information Lookup: Get details on drugs including usage, dosage, side effects, and interactions
AI Chat Assistant: Ask general health-related questions in a conversational format
Fallback Mode: Provides demo responses when AI services are unavailable
Tech Stack

Backend

Flask
psycopg2
bcrypt
APScheduler

Database

PostgreSQL

AI Integration

Groq API
Llama 3.1 / Llama 3.2 Vision models

Frontend

Jinja2
Tailwind CSS
Material Design Icons

Deployment

Railway
Features Summary
Secure authentication system
Medication CRUD operations
Smart reminders and scheduling
Adherence tracking dashboard
Export and printable reports
AI-powered health assistant
Responsive UI with dark mode support
Live Application

URL: https://medtracker.up.railway.app/

Deployed using Railway.

Note: The free tier may take a few seconds to load on first visit.
