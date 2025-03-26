#!/usr/bin/env python3
# src/verify_diagram_migration.py
from database import db

def verify_diagram_migration():
    """
    Verify the successful migration of diagram questions to the database.
    Prints counts of total questions and breakdown by subject.
    """
    print("Verifying diagram question migration...")
    
    # Get total count
    result = db.client.table('diagram_questions').select('count', count='exact').execute()
    total_count = result.count if hasattr(result, 'count') else 0
    print(f"\nTotal diagram questions in database: {total_count}")
    
    # Get count by subject
    subjects = [
        'Digital Logic',
        'Computer Networks',
        'Machine Learning',
        'Cloud Computing',
    ]
    
    print("\nBreakdown by subject:")
    for subject in subjects:
        result = db.client.table('diagram_questions')\
            .select('count', count='exact')\
            .eq('subject', subject)\
            .execute()
        count = result.count if hasattr(result, 'count') else 0
        print(f"{subject}: {count} diagram questions")
    
    # Verify SVG content presence
    print("\nVerifying SVG content:")
    result = db.client.table('diagram_questions')\
        .select('count', count='exact')\
        .is_('svg_code', 'null')\
        .execute()
    missing_svg = result.count if hasattr(result, 'count') else 0
    
    if missing_svg > 0:
        print(f"Warning: Found {missing_svg} diagram questions with missing SVG code!")
    else:
        print("All diagram questions have SVG code content.")

if __name__ == "__main__":
    verify_diagram_migration() 