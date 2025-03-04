# src/migrate_questions.py
import json
import os
from database import db

def migrate_questions():
    processed_dir = 'data/processed'
    subjects = {
        'mock_engineering_maths.json': 'Engineering Mathematics',
        'mock_digital_logic.json': 'Digital Logic',
        'mock_computer_networks.json': 'Computer Networks',
        'mock_machine_learning.json': 'Machine Learning',
        'mock_software_engineering.json': 'Software Engineering',
        'mock_cloud_computing.json': 'Cloud Computing',
        'mock_cybersecurity.json': 'Cybersecurity',
        'mock_aptitude_and_reasoning.json': 'Aptitude and Reasoning'
    }

    for filename, subject in subjects.items():
        filepath = os.path.join(processed_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                questions = data['questions']
                
                for q in questions:
                    # Format question for database
                    question_data = {
                        'subject': subject,
                        'question_type': 'single_answer',
                        'question': q['question'],
                        'options': q['options'],
                        'correct_answer': q['correct_answer'],
                        'explanation': q['explanation']
                    }
                    
                    # Insert into database (removed await)
                    db.client.table('mock_questions').insert(question_data).execute()
                
                print(f"Successfully migrated questions for {subject}")
                
        except FileNotFoundError:
            print(f"Warning: File not found for {subject} at {filepath}")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for {subject}: {str(e)}")
        except Exception as e:
            print(f"Error migrating {subject}: {str(e)}")

if __name__ == "__main__":
    migrate_questions()