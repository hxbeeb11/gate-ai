from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        """Initialize Supabase client."""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials. Please check your .env file.")
        
        print(f"Connecting to Supabase URL: {self.supabase_url}")
        self.client = create_client(self.supabase_url, self.supabase_key)
        
        # Verify connection
        try:
            # Try to make a simple query to verify connection
            self.client.auth.get_user()
            print("Successfully connected to Supabase")
        except Exception as e:
            print(f"Warning: Could not verify Supabase connection: {str(e)}")
    
    def create_user(self, user_id: str, email: str) -> Dict:
        """Create a new user record."""
        data = {
            'id': user_id,
            'email': email,
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat()
        }
        
        return self.client.table('users').insert(data).execute()
    
    def update_user_login(self, user_id: str) -> Dict:
        """Update user's last login time."""
        return self.client.table('users').update({
            'last_login': datetime.now().isoformat()
        }).eq('id', user_id).execute()
    
    def get_user_progress(self, user_id: str) -> List[Dict]:
        """Get user's progress for all subjects."""
        return self.client.table('subject_progress').select('*').eq('user_id', user_id).execute()
    
    def update_subject_progress(
        self,
        user_id: str,
        subject: str,
        score: float,
        difficulty_level: str,
        mastered: bool = False
    ) -> Dict:
        """Update user's progress in a subject."""
        data = {
            'user_id': user_id,
            'subject': subject,
            'current_score': score,
            'difficulty_level': difficulty_level,
            'mastered': mastered,
            'last_attempt': datetime.now().isoformat()
        }
        
        # Try to update existing record
        result = self.client.table('subject_progress').update(data).eq(
            'user_id', user_id
        ).eq('subject', subject).execute()
        
        # If no record exists, create new one
        if not result.data:
            result = self.client.table('subject_progress').insert(data).execute()
        
        return result
    
    def add_test_result(
        self,
        user_id: str,
        subject: str,
        score: float,
        difficulty_level: str,
        time_taken: float,
        num_questions: int,
        correct_answers: int
    ) -> Dict:
        """Add a new test result."""
        data = {
            'user_id': user_id,
            'subject': subject,
            'score': score,
            'difficulty_level': difficulty_level,
            'time_taken': time_taken,
            'num_questions': num_questions,
            'correct_answers': correct_answers,
            'test_date': datetime.now().isoformat()
        }
        
        return self.client.table('test_history').insert(data).execute()
    
    def get_test_history(
        self,
        user_id: str,
        subject: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get user's test history."""
        query = self.client.table('test_history').select('*').eq('user_id', user_id)
        
        if subject:
            query = query.eq('subject', subject)
        
        return query.order('test_date', desc=True).limit(limit).execute()

# Create a singleton instance
db = Database() 