import json
import numpy as np
from typing import List, Dict, Tuple
import os
from datetime import datetime
import math

class AdaptiveLearningSystem:
    def __init__(self, data_dir: str = None):
        # Get the directory where this file is located (src)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go one level up to the project root
        project_root = os.path.dirname(current_dir)
        
        # Set data_dir relative to project root
        if data_dir is None:
            data_dir = os.path.join(project_root, 'data')
        
        self.data_dir = data_dir
        self.topics_path = os.path.join(data_dir, 'raw', 'topics.json')
        self.state_dir = os.path.join(data_dir, 'adaptive_state')
        os.makedirs(self.state_dir, exist_ok=True)
        
        # Create data directories if they don't exist
        os.makedirs(os.path.join(data_dir, 'raw'), exist_ok=True)
        os.makedirs(os.path.join(data_dir, 'processed'), exist_ok=True)
        
        # Load topics data
        self.load_data()
        
        # Define difficulty levels with new threshold
        self.difficulty_levels = {
            'beginner': 0.7,     # Need to score above 70% to advance
            'intermediate': 0.7,  # Need to score above 70% to advance
            'advanced': 0.7      # Need to score above 70% to master
        }
        
    def load_data(self):
        """Load topics data from file."""
        try:
            with open(self.topics_path, 'r', encoding='utf-8') as f:
                self.topics_data = json.load(f)
            print(f"Successfully loaded topics from {self.topics_path}")
            print(f"Available subjects: {[topic['title'] for topic in self.topics_data.get('topics', [])]}")
        except Exception as e:
            print(f"Error loading topics data: {str(e)}")
            self.topics_data = {'topics': []}

    def clear_user_state(self, user_id: str):
        """Clear the user's learning state."""
        try:
            state_path = os.path.join(self.state_dir, f'user_{user_id}_state.json')
            if os.path.exists(state_path):
                os.remove(state_path)
                print(f"Cleared user state for user {user_id}")
            return self.get_user_state(user_id)  # Return fresh state
        except Exception as e:
            print(f"Error clearing user state: {str(e)}")
            return None

    def get_user_state(self, user_id: str) -> Dict:
        """Get or create user's learning state."""
        state_path = os.path.join(self.state_dir, f'user_{user_id}_state.json')
        
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                return json.load(f)
        
        # Initialize new user state
        initial_state = {
            'user_id': user_id,
            'topic_scores': {},
            'questions_answered': [],
            'learning_path': [],
            'current_level': 1,
            'timestamp': datetime.now().isoformat()
        }
        
        # Initialize scores for all topics with difficulty levels
        for topic in self.topics_data.get('topics', []):
            for subtopic in topic.get('subtopics', []):
                topic_key = f"{topic['title']} - {subtopic['title']}"
                initial_state['topic_scores'][topic_key] = {
                    'score': 0.0,
                    'attempts': 0,
                    'correct': 0,
                    'last_attempt': None,
                    'difficulty_level': 'beginner',
                    'mastered': False,
                    'subtopics': {}
                }
        
        self.save_user_state(user_id, initial_state)
        return initial_state
    
    def save_user_state(self, user_id: str, state: Dict):
        """Save user's learning state to file."""
        state_path = os.path.join(self.state_dir, f'user_{user_id}_state.json')
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def update_topic_score(self, user_id: str, topic: str, correct: bool, time_taken: float):
        """Update user's score and difficulty level for a topic."""
        state = self.get_user_state(user_id)
        
        # Split topic to get subject
        subject = topic.split(' - ')[0]
        
        # Update subject state if not exists
        if subject not in state['topic_scores']:
            state['topic_scores'][subject] = {
                'score': 0.0,
                'attempts': 0,
                'correct': 0,
                'last_attempt': None,
                'difficulty_level': 'beginner',
                'mastered': False,
                'subtopics': {}
            }
        
        subject_state = state['topic_scores'][subject]
        
        # Update statistics
        subject_state['attempts'] += 1
        if correct:
            subject_state['correct'] += 1
        
        # Calculate new score (percentage correct)
        new_score = correct  # This is already a percentage from the frontend
        
        # Apply exponential moving average
        alpha = 0.3
        subject_state['score'] = alpha * new_score + (1 - alpha) * subject_state['score']
        subject_state['last_attempt'] = datetime.now().isoformat()
        
        # Update difficulty level based on score
        current_level = subject_state['difficulty_level']
        threshold = self.difficulty_levels[current_level]
        difficulty_changed = False
        
        if new_score >= threshold:
            if current_level == 'beginner':
                subject_state['difficulty_level'] = 'intermediate'
                difficulty_changed = True
            elif current_level == 'intermediate':
                subject_state['difficulty_level'] = 'advanced'
                difficulty_changed = True
            elif current_level == 'advanced':
                subject_state['mastered'] = True
                difficulty_changed = True
            
            if difficulty_changed:
                # Reset score when advancing to next level
                subject_state['score'] = 0.0
                subject_state['correct'] = 0
                subject_state['attempts'] = 0
        
        self.save_user_state(user_id, state)
        return {
            'score': new_score,
            'current_difficulty': subject_state['difficulty_level'],
            'threshold_met': new_score >= threshold,
            'threshold': threshold,
            'difficulty_changed': difficulty_changed
        }
    
    def get_topic_recommendations(self, user_id: str, n: int = 3) -> List[str]:
        """Get recommended topics for the user based on their performance."""
        state = self.get_user_state(user_id)
        topic_scores = state['topic_scores']
        
        # Calculate priority scores for each topic
        priorities = []
        for topic, stats in topic_scores.items():
            # Base priority on inverse of current score
            priority = 1 - stats['score']
            
            # Adjust priority based on attempts
            if stats['attempts'] == 0:
                priority *= 1.2  # Boost priority for untried topics
            
            # Adjust priority based on time since last attempt
            if stats['last_attempt']:
                last_attempt = datetime.fromisoformat(stats['last_attempt'])
                days_since = (datetime.now() - last_attempt).days
                priority *= (1 + 0.1 * days_since)  # Increase priority for topics not attempted recently
            
            priorities.append((topic, priority))
        
        # Sort by priority and return top N topics
        priorities.sort(key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in priorities[:n]]
    
    def get_questions_for_topic(self, topic: str, n: int = 5) -> List[Dict]:
        """This method is deprecated as we now generate questions using the API."""
        return []  # Return empty list as questions are generated via API
    
    def generate_learning_path(self, user_id: str) -> List[Dict]:
        """Generate a personalized learning path based on progressive difficulty."""
        state = self.get_user_state(user_id)
        
        # Group topics by main subject and difficulty
        topics_by_subject = {}
        for topic in self.topics_data['topics']:
            subject = topic['title']
            if subject not in topics_by_subject:
                topics_by_subject[subject] = {
                    'beginner': [],
                    'intermediate': [],
                    'advanced': []
                }
            
            # Get subject progress from state
            for subtopic in topic['subtopics']:
                topic_key = f"{subject} - {subtopic['title']}"
                stats = state['topic_scores'].get(topic_key, {
                    'score': 0.0,
                    'attempts': 0,
                    'difficulty_level': 'beginner',
                    'mastered': False
                })
                topics_by_subject[subject][stats['difficulty_level']].append((topic_key, stats, subtopic))
        
        learning_path = []
        
        # For each subject, select appropriate difficulty topics
        for subject in topics_by_subject:
            # First try to find unmastered topics at current difficulty
            for level in ['beginner', 'intermediate', 'advanced']:
                topics = topics_by_subject[subject][level]
                unmastered_topics = [(t, s, st) for t, s, st in topics if not s['mastered']]
                
                if unmastered_topics:
                    # Sort by score and take the lowest scoring topic
                    topic_key, stats, subtopic = sorted(unmastered_topics, key=lambda x: x[1]['score'])[0]
                    
                    learning_path.append({
                        'topic': topic_key,
                        'key_points': subtopic['key_points'],
                        'examples': subtopic.get('examples', []),
                        'current_score': stats['score'],
                        'difficulty_level': stats['difficulty_level'],
                        'attempts': stats['attempts']
                    })
                    break  # Move to next subject
        
        # Sort learning path to prioritize lower difficulty levels
        difficulty_order = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
        learning_path.sort(key=lambda x: (difficulty_order[x['difficulty_level']], -x['current_score']))
        
        # Limit to 8 topics
        learning_path = learning_path[:8]
        
        state['learning_path'] = learning_path
        self.save_user_state(user_id, state)
        return learning_path
    
    def get_progress_report(self, user_id: str) -> Dict:
        """Generate a progress report showing subject-level progress."""
        state = self.get_user_state(user_id)
        
        # Group topics by main subject
        subjects = {}
        for topic, stats in state['topic_scores'].items():
            subject = topic.split(' - ')[0]
            if subject not in subjects:
                subjects[subject] = {
                    'difficulty_level': 'beginner',
                    'score': 0.0,
                    'topics_completed': 0,
                    'total_topics': 0
                }
            
            subjects[subject]['total_topics'] += 1
            if stats['score'] > 0:
                subjects[subject]['topics_completed'] += 1
                subjects[subject]['score'] = max(subjects[subject]['score'], stats['score'])
            
            # Update subject difficulty level based on topic progress
            if stats['difficulty_level'] == 'advanced':
                subjects[subject]['difficulty_level'] = 'advanced'
            elif stats['difficulty_level'] == 'intermediate' and subjects[subject]['difficulty_level'] == 'beginner':
                subjects[subject]['difficulty_level'] = 'intermediate'
        
        return {
            'user_id': user_id,
            'subjects': subjects,
            'timestamp': datetime.now().isoformat()
        }

def main():
    # Example usage
    adaptive_system = AdaptiveLearningSystem()
    
    # Test with a sample user
    user_id = "test_user_1"
    
    # Generate learning path
    learning_path = adaptive_system.generate_learning_path(user_id)
    print(f"Generated learning path with {len(learning_path)} topics")
    
    # Simulate some question answers
    for topic in learning_path:
        # Simulate answering questions correctly 70% of the time
        for _ in range(5):
            correct = np.random.random() < 0.7
            time_taken = np.random.uniform(30, 180)  # Random time between 30s and 3m
            adaptive_system.update_topic_score(user_id, topic['topic'], correct, time_taken)
    
    # Get progress report
    progress = adaptive_system.get_progress_report(user_id)
    print("\nProgress Report:")
    print(f"Total Topics: {progress['subjects']['total_topics']}")
    print(f"Topics Completed: {progress['subjects']['topics_completed']}")
    print(f"Average Score: {progress['subjects']['score']:.2f}")
    print("\nSubjects:")
    for subject, stats in progress['subjects'].items():
        print(f"- {subject}:")
        print(f"  Difficulty Level: {stats['difficulty_level']}")
        print(f"  Topics Completed: {stats['topics_completed']}")
        print(f"  Total Topics: {stats['total_topics']}")
        print(f"  Average Score: {stats['score']:.2f}")

if __name__ == "__main__":
    main() 