HiredSense – AI Resume ATS and Job Matching System

HiredSense is a production-ready backend system that simulates a real-world Applicant Tracking System (ATS).
It helps candidates understand how well their resumes match job requirements and helps recruiters shortlist candidates efficiently.

The platform calculates ATS scores, identifies missing skills, ranks relevant jobs, and generates interview preparation content using secure and scalable REST APIs.

---

Problem Statement

Most job seekers apply for jobs without knowing how ATS systems evaluate resumes.
They are unaware of skill gaps and often struggle with interview preparation.

Recruiters receive a high volume of resumes and need a fast and automated way to match candidates with job requirements.

HiredSense solves both problems by automating resume evaluation and job matching.

---

How the System Works

Users upload resumes in PDF format.
The system stores the file and extracts useful text from it.

Relevant skills are identified from the resume content.

Recruiters create job postings with required skills and descriptions.

The system compares resume skills with job requirements, calculates an ATS score, and identifies missing skills.

Jobs are ranked based on relevance and ATS score.

Interview questions are generated based on matched and missing skills.

---

Authentication and Security

The system uses JWT based authentication with access and refresh tokens.
Session authentication is also used for the frontend UI.

Role-based access control is implemented:
Candidates can manage resumes and view matches.
Recruiters can manage job postings.

All APIs are protected and require authentication.

---

API Documentation

Interactive API documentation is available using Swagger:

[http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)

It includes authentication endpoints, resume APIs, job APIs, and matching endpoints.

---

Tech Stack

Backend:
Django
Django REST Framework
JWT Authentication

Frontend:
Django Templates
Bootstrap

Database:
SQLite for local development
PostgreSQL ready for production

Deployment:
Render
Gunicorn
WhiteNoise

---

Key Features

Resume upload and parsing
ATS score calculation
Skill gap analysis
Job ranking system
Interview question generation
JWT authentication
Role-based permissions
Search, pagination, and filtering
Production-ready configuration

---

Security Best Practices

Environment variables are used for sensitive data.
Passwords are securely hashed.
All APIs require authentication.
Secrets and media files are excluded from Git.

---

Setup Instructions

Clone the repository.
Install dependencies from requirements.txt.
Run database migrations.
Create a superuser.
Start the development server.

---

JWT Usage

Generate token using /api/token/
Use Authorization header:

Bearer your_access_token

---

Main Endpoints

Authentication: /api/token/
Dashboard stats: /api/dashboard-stats/
Resumes: /api/resumes/
Jobs: /api/jobs/
Job matches: /api/jobs/{id}/matches/

---

Future Improvements

Recruiter analytics dashboard
Resume improvement suggestions
Cloud file storage
Advanced NLP matching
External job API integrations

---

Author

Yash Gandhi

This project demonstrates real-world backend development including authentication, role-based access control, scalable API design, and automated ATS workflows.

