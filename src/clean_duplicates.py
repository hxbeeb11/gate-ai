# src/clean_duplicates.py
from database import db

def clean_duplicates():
    print("Cleaning duplicate questions...")
    
    # First, let's identify duplicates
    subjects = [
        'Engineering Mathematics',
        'Digital Logic',
        'Computer Networks',
        'Machine Learning',
        'Software Engineering',
        'Cloud Computing',
        'Cybersecurity',
        'Aptitude and Reasoning'
    ]
    
    for subject in subjects:
        # Get all questions for this subject
        result = db.client.table('mock_questions')\
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
                db.client.table('mock_questions')\
                    .delete()\
                    .in_('id', duplicate_ids)\
                    .execute()
                
                print(f"Removed {len(duplicate_ids)} duplicate(s) from {subject}")

if __name__ == "__main__":
    clean_duplicates()