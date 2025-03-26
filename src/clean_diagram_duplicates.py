#!/usr/bin/env python3
# src/clean_diagram_duplicates.py
from database import db

def clean_diagram_duplicates():
    """
    Identify and remove duplicate diagram questions from the diagram_questions table.
    Duplicates are identified by having the same question text within the same subject.
    """
    print("Cleaning duplicate diagram questions...")
    
    # Subjects with diagram questions
    subjects = [
        'Digital Logic',
        'Computer Networks',
        'Machine Learning',
        'Cloud Computing',
    ]
    
    total_duplicates = 0
    
    for subject in subjects:
        # Get all questions for this subject
        result = db.client.table('diagram_questions')\
            .select('question, id')\
            .eq('subject', subject)\
            .execute()
        
        if hasattr(result, 'data'):
            questions = result.data
            seen_questions = set()
            duplicate_ids = []
            
            # Find duplicates
            for q in questions:
                if q['question'] in seen_questions:
                    duplicate_ids.append(q['id'])
                else:
                    seen_questions.add(q['question'])
            
            # Delete duplicates
            if duplicate_ids:
                db.client.table('diagram_questions')\
                    .delete()\
                    .in_('id', duplicate_ids)\
                    .execute()
                
                print(f"Removed {len(duplicate_ids)} duplicate(s) from {subject}")
                total_duplicates += len(duplicate_ids)
    
    print(f"\nTotal duplicates removed: {total_duplicates}")
    
    # After cleaning duplicates, verify SVG content integrity
    result = db.client.table('diagram_questions')\
        .select('id, subject')\
        .is_('svg_code', 'null')\
        .execute()
    
    if hasattr(result, 'data') and result.data:
        print(f"\nWarning: Found {len(result.data)} questions with missing SVG content after cleanup.")
        for item in result.data:
            print(f"  - ID: {item['id']}, Subject: {item['subject']}")
    else:
        print("\nAll remaining diagram questions have valid SVG content.")

if __name__ == "__main__":
    clean_diagram_duplicates() 