HiredSense – AI Resume ATS and Job Matching System

HiredSense is a hiring support system that helps candidates understand how their resumes perform against job requirements. The platform analyzes resumes, calculates ATS scores, matches candidates with relevant jobs, identifies missing skills, and generates interview preparation questions.

The goal of this project is to simulate a real-world Applicant Tracking System workflow in a simple and practical way.



Problem Statement

Most job seekers do not know how ATS systems evaluate resumes. They apply without understanding whether their skills actually match job requirements and struggle with interview preparation.

Recruiters, on the other hand, receive many resumes and need a quick way to shortlist candidates based on skills.

HiredSense addresses both problems by automating resume evaluation and job matching.



How the System Works

1. Resume Upload  
Users upload their resumes in PDF or DOCX format. The system stores the file and extracts text from it.

2. Resume Parsing and Skill Extraction  
The extracted text is cleaned and processed. Relevant technical skills are identified from the resume.

3. Job Creation  
Jobs are created by an admin or recruiter. Each job contains required skills and a detailed description.

4. ATS Matching Logic  
The system compares resume skills with job-required skills.  
An ATS score is calculated as a percentage match.  
Missing skills are also identified.

5. Job Recommendations  
Jobs are ranked based on ATS score.  
Users see the most relevant jobs first.

6. Interview Preparation  
Based on the matched and missing skills, interview questions are generated.  
Ideal answers are also provided to help candidates prepare.



Tech Stack Used

Backend  
Django  
Django REST Framework  
Python  
Basic machine learning logic using scikit-learn

Frontend  
Django Templates  
Bootstrap

Database  
SQLite for local development  
PostgreSQL for production

Deployment  
Render  
Gunicorn  
WhiteNoise



Key Features

Resume upload and parsing  
ATS score calculation  
Skill gap analysis  
Job matching and ranking  
Interview question generation  
User authentication and authorization  
Pagination, search, and ordering  
Production-ready deployment setup



Security and Best Practices

Environment variables are used for sensitive data  
.env, media files, and database files are not committed to Git  
Authentication is enforced on all API endpoints  
HTTPS is handled at the production proxy level



Deployment Notes

The project is deployed on Render using Gunicorn as the WSGI server.  
Static files are served using WhiteNoise.

For demonstration purposes, user-uploaded files are stored locally.  
In a scalable production environment, this can be extended to cloud storage such as AWS S3 or Cloudinary.



Use Cases

Internship and entry-level hiring systems  
Resume evaluation tools  
Career guidance platforms  
ATS workflow demonstrations



Future Improvements

Recruiter dashboard  
Integration with external job APIs  
Resume improvement suggestions  
Cloud-based file storage  
Advanced NLP and ML models



Author

Yash Gandhi

This project was built to demonstrate real-world ATS logic, resume evaluation, and job matching workflows in a production-oriented Django application.
