import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from together import Together
from dotenv import load_dotenv
import asyncio

class QuestionGenerator:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the question generator with Together AI API settings."""
        # Get the directory where this file is located (src)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go one level up to the project root
        self.project_root = os.path.dirname(current_dir)
        
        # Load environment variables
        load_dotenv(os.path.join(self.project_root, '.env'))
        
        # Initialize Together client
        self.api_key = api_key or os.getenv('TOGETHER_API_KEY')
        self.client = Together(api_key=self.api_key)
        self.model = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"

    def _create_prompt(self, topic_data: Dict, num_questions: int = 5) -> str:
        """Create a prompt for the Llama model based on topic data."""
        prompt = f"""Generate {num_questions} multiple choice questions for the topic "{topic_data['title']}" based on these key points:

Key points to cover:
{chr(10).join('- ' + point for point in topic_data['key_points'])}

Format each question as a JSON object with this structure:
{{
    "questions": [
        {{
            "question": "The technical question text",
            "options": ["option1", "option2", "option3", "option4"],
            "correct_answer": 0,  // Index of correct option (0-3)
            "explanation": "Detailed explanation of why this is the correct answer"
        }}
    ]
}}
"""
        return prompt

    async def generate_questions_for_topic(self, topic: str, num_questions: int = 5, difficulty_level: str = 'beginner') -> List[Dict]:
        """Generate questions for a specific topic."""
        try:
            # Load topics data
            topics_path = os.path.join(self.project_root, 'data', 'raw', 'topics.json')
            with open(topics_path, 'r', encoding='utf-8') as f:
                topics_data = json.load(f)
            
            # Parse topic string (format: "Subject - Subtopic" or just "Subject")
            parts = topic.split(' - ')
            subject = parts[0]
            subtopic_title = parts[1] if len(parts) > 1 else None
            
            # Find all subtopics for the subject
            subject_data = None
            target_subtopic = None
            for t in topics_data['topics']:
                if t['title'] == subject:
                    subject_data = t
                    if subtopic_title:
                        for st in t['subtopics']:
                            if st['title'] == subtopic_title:
                                target_subtopic = st
                                break
                    break
            
            if not subject_data:
                raise ValueError(f"Subject {subject} not found")
            
            if subtopic_title and not target_subtopic:
                raise ValueError(f"Subtopic {subtopic_title} not found in {subject}")

            # Define difficulty-specific instructions
            difficulty_guidelines = {
                'beginner': """
                    - Focus on basic definitions and core concepts
                    - Use straightforward questions testing fundamental understanding
                    - Avoid complex scenarios or multi-step problems
                    - Include simple application of concepts
                    - Use clear and direct language
                """,
                'intermediate': """
                    - Combine multiple concepts in questions
                    - Include practical applications and case studies
                    - Test analytical thinking and problem-solving
                    - Use moderately complex scenarios
                    - Require deeper understanding of relationships between concepts
                """,
                'advanced': """
                    - Present complex scenarios requiring deep analysis
                    - Include edge cases and special conditions
                    - Require integration of multiple concepts
                    - Test advanced problem-solving abilities
                    - Include GATE exam level complexity
                    - Focus on optimization and best practices
                """
            }
            
            # Create prompt based on whether we're generating questions for a specific subtopic or the whole subject
            if target_subtopic:
                # Generate questions for specific subtopic
                prompt = f"""You are a technical question generator for GATE exam preparation.
Generate {num_questions} multiple choice questions for the subtopic "{target_subtopic['title']}" in subject "{subject}".

Current difficulty level is {difficulty_level}. Follow these guidelines for this level:
{difficulty_guidelines[difficulty_level]}

Key points to cover:
{chr(10).join('- ' + point for point in target_subtopic['key_points'])}

Important Instructions:
1. Questions MUST match the {difficulty_level} difficulty level guidelines above
2. Each question should be more challenging than beginner level questions
3. Include practical applications and real-world scenarios
4. Ensure explanations are detailed and educational

Return ONLY a JSON object with this exact structure:
{{
    "questions": [
        {{
            "question": "question text here",
            "options": ["option1", "option2", "option3", "option4"],
            "correct_answer": 0,
            "explanation": "explanation here"
        }}
    ]
}}"""
            else:
                # Generate questions for the whole subject
                all_key_points = []
                for st in subject_data['subtopics']:
                    all_key_points.extend([f"[{st['title']}] {point}" for point in st['key_points']])
                
                prompt = f"""You are a technical question generator for GATE exam preparation.
Generate {num_questions} multiple choice questions for the subject "{subject}".

Current difficulty level is {difficulty_level}. Follow these guidelines for this level:
{difficulty_guidelines[difficulty_level]}

Key points to cover across subtopics:
{chr(10).join('- ' + point for point in all_key_points)}

Important Instructions:
1. Questions MUST match the {difficulty_level} difficulty level guidelines above
2. Each question should be more challenging than beginner level questions
3. Include practical applications and real-world scenarios
4. Ensure explanations are detailed and educational
5. Generate questions that cover different subtopics
6. Make sure questions are balanced across subtopics
7. Include the subtopic name in the explanation when relevant

Return ONLY a JSON object with this exact structure:
{{
    "questions": [
        {{
            "question": "question text here",
            "options": ["option1", "option2", "option3", "option4"],
            "correct_answer": 0,
            "explanation": "explanation here"
        }}
    ]
}}"""            
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical question generator specialized in creating GATE exam questions. You must respond with a complete, valid JSON object containing questions. Your response must be a properly formatted JSON with no additional text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.7,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.1,
                stop=None
            )
            
            # Extract content from response
            content = response.choices[0].message.content.strip()
            
            try:
                # Parse JSON directly
                questions_data = json.loads(content)
                
                if not isinstance(questions_data, dict) or 'questions' not in questions_data:
                    raise ValueError("Response is not in the expected format")
                
                # Validate and add metadata to questions
                valid_questions = []
                for q in questions_data['questions']:
                    if all(key in q for key in ['question', 'options', 'correct_answer', 'explanation']):
                        q['topic'] = topic  # Use full topic string
                        q['subject'] = subject
                        valid_questions.append(q)
                
                if not valid_questions:
                    raise ValueError("No valid questions found in response")
                
                return valid_questions
                
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON response from API")
            
        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            raise Exception(f"Failed to generate questions: {str(e)}")

def main():
    """Test the question generator."""
    async def test():
        generator = QuestionGenerator()
        try:
            questions = await generator.generate_questions_for_topic(
                topic="Engineering Mathematics - Discrete Mathematics",
                num_questions=3
            )
            print(json.dumps(questions, indent=2))
        except Exception as e:
            print(f"Error: {str(e)}")

    # Run the test
    asyncio.run(test())

if __name__ == "__main__":
    main() 