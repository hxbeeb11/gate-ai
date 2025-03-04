# src/verify_migration.py
from database import db

def verify_migration():
    print("Verifying question migration...")
    
    # Get total count
    result = db.client.table('mock_questions').select('count', count='exact').execute()
    total_count = result.count if hasattr(result, 'count') else 0
    print(f"\nTotal questions in database: {total_count}")
    
    # Get count by subject
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
    
    print("\nBreakdown by subject:")
    for subject in subjects:
        result = db.client.table('mock_questions')\
            .select('count', count='exact')\
            .eq('subject', subject)\
            .execute()
        count = result.count if hasattr(result, 'count') else 0
        print(f"{subject}: {count} questions")

if __name__ == "__main__":
    verify_migration()