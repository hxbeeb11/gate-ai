#!/usr/bin/env python3
# src/migrate_diagram_questions.py
import json
import os
from database import db

def migrate_diagram_questions():
    """
    Migrate diagram questions from JSON files in data/processed/diagrams
    to the diagram_questions table in the database.
    """
    processed_dir = 'data/processed/diagrams'
    
    # Define the subjects corresponding to the JSON files
    subjects = {
        'digital_logic_diagram_questions.json': 'Digital Logic',
        'computer_networks_diagram_questions.json': 'Computer Networks',
        'machine_learning_diagram_questions.json': 'Machine Learning',
        'cloud_computing_diagram_questions.json': 'Cloud Computing',
    }

    for filename, subject in subjects.items():
        filepath = os.path.join(processed_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                questions = data['diagram_questions']
                
                print(f"Found {len(questions)} diagram questions for {subject}")
                
                for q in questions:
                    # Format question for database
                    question_data = {
                        'subject': subject,
                        'question': q['question'],
                        'options': q['options'],
                        'correct_answer': q['correct_answer'],
                        'explanation': q['explanation'],
                        'svg_code': q['svg_code']
                    }
                    
                    # Insert into database
                    result = db.client.table('diagram_questions').insert(question_data).execute()
                    
                    if not result.data:
                        print(f"Warning: Failed to insert a question for {subject}")
                
                print(f"Successfully migrated diagram questions for {subject}")
                
        except FileNotFoundError:
            print(f"Warning: File not found for {subject} at {filepath}")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for {subject}: {str(e)}")
        except Exception as e:
            print(f"Error migrating {subject}: {str(e)}")

if __name__ == "__main__":
    migrate_diagram_questions() 