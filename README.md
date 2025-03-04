# GATE AI - Adaptive Learning System

GATE AI is an intelligent adaptive learning platform designed to help students prepare for GATE (Graduate Aptitude Test in Engineering) examinations. The system leverages advanced NLP techniques, including BERT-based models and Together AI's LLM API, to provide personalized learning experiences through adaptive question generation and intelligent progress tracking.

## Key Features

- **Adaptive Learning Path**: 
  - Automatically adjusts difficulty levels based on user performance.
  - Three-tier progression system: Beginner → Intermediate → Advanced.
  - Personalized topic recommendations based on user progress.

- **Smart Question Generation**: 
  - Generates multiple choice questions tailored to the user's current difficulty level.
  - Incorporates detailed guidelines for question complexity based on difficulty.
  - Provides practical applications and real-world scenarios in questions.

- **Comprehensive Progress Tracking**: 
  - Subject-wise progress monitoring.
  - Detailed performance analytics.
  - Learning path visualization.
  - Difficulty level progression tracking.

- **Subject Coverage**:
  - Engineering Mathematics
  - Digital Logic
  - Computer Networks
  - Machine Learning
  - Software Engineering
  - Cloud Computing & Big Data
  - Cybersecurity

## Quick Start Guide

1. **System Requirements**:
   - Python 3.8 or higher
   - 8GB RAM minimum (16GB recommended)
   - Internet connection for API access
   - Windows 10/11 or Linux

2. **Installation and Setup**:
   ```bash
   # Clean previous installation (if any)
   rm -rf venv models  # Unix/Linux
   # OR
   rmdir /s /q venv models  # Windows

   # Run setup script (this will create venv and install all requirements)
   python setup.py
   ```

3. **Start the Application**:
   ```bash
   # Activate the virtual environment (created by setup.py)
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate # Unix/Linux

   # Train BERT model (required only once)
   python src/train_bert.py

   # Start the Flask application
   python src/app.py
   ```

4. **Access the Application**:
   - Open web browser
   - Visit `http://127.0.0.1:5000`
   - Start with any subject from the learning path

## Detailed Usage Guide

### 1. Dashboard Overview

The main dashboard is divided into two sections:
- **Left Panel**: Subject Progress
  - Shows all subjects with their current status.
  - Displays difficulty levels and scores.
  - Click on subject names to expand details.

- **Right Panel**: Learning Path
  - Recommended topics based on your progress.
  - Difficulty-appropriate content.
  - "Start Learning" buttons for each topic.

### 2. Learning Process

1. **Select a Topic**:
   - Choose from recommended learning path.
   - Or select any subject from progress panel.
   - Click "Start Learning" to begin.

2. **Question Session**:
   - Multiple choice questions.
   - Contextual explanations.
   - Real-time feedback.
   - Progress tracking.

3. **Progress System**:
   - **Beginner Level**:
     - Score 70% or higher to advance.
     - Focus on basic concepts.
     - Simplified question format.

   - **Intermediate Level**:
     - More complex questions.
     - Application-based problems.
     - 70% required for Advanced.

   - **Advanced Level**:
     - GATE-level complexity.
     - Integrated concept testing.
     - Mastery achievement tracking.

### 3. Best Practices

- Start with fundamental topics.
- Complete all questions in a session.
- Review explanations thoroughly.
- Retry topics until 70% mastery.
- Follow the recommended path.
- Track progress regularly.

## Troubleshooting

### Common Issues and Solutions

1. **Setup Issues**:
   ```bash
   # If setup.py fails
   pip install --upgrade pip
   python setup.py

   # If NLTK data download fails
   python -m nltk.downloader punkt stopwords wordnet
   ```

2. **Model Training Issues**:
   ```bash
   # If train_bert.py fails
   rm -rf models/*
   python src/train_bert.py
   ```

3. **Application Issues**:
   - Check .env file for API keys.
   - Ensure all directories exist.
   - Verify internet connection.
   - Check Python version compatibility.

### Error Messages

- "No module named 'xyz'": Run setup.py again.
- "API key not found": Check .env file.
- "Model not found": Run train_bert.py.
- "Port already in use": Close other applications using port 5000.

## Data Management

- **Study Materials**: `/data/raw/`
- **Processed Data**: `/data/processed/`
- **User Progress**: `/data/adaptive_state/`
- **Model Files**: `/models/`

## Contributing

1. Fork the repository.
2. Create feature branch.
3. Make changes.
4. Submit pull request.

## Support

For additional help:
1. Check documentation.
2. Review error logs.
3. Ensure prerequisites.
4. Contact support team. 