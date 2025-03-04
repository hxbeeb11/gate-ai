import json
import random
import os
from dotenv import load_dotenv
from together import Together
import re
from database import db

# Load environment variables and initialize Together AI client
load_dotenv()
together_client = Together(api_key=os.getenv('TOGETHER_API_KEY'))

async def get_questions_from_db(subject: str, count: int) -> list:
    """
    Fetch random questions from database for a specific subject.
    Returns in the same format as the current JSON structure.
    """
    try:
        # Use a different approach for random selection
        result = db.client.table('mock_questions')\
            .select('*')\
            .eq('subject', subject)\
            .execute()
        
        if not result.data:
            print(f"Warning: No questions found in database for {subject}")
            return []
            
        # Randomly select questions in Python
        selected_questions = random.sample(result.data, min(count, len(result.data)))
        
        # Format questions to match current structure
        questions = []
        for q in selected_questions:
            questions.append({
                'question': q['question'],
                'options': q['options'],
                'correct_answer': q['correct_answer'],
                'explanation': q['explanation'],
                'subject': q['subject'],
                'type': 'single_answer'
            })
        
        print(f"Successfully fetched {len(questions)} questions for {subject}")
        return questions
        
    except Exception as e:
        print(f"Error fetching questions from database for {subject}: {str(e)}")
        return []

def generate_advanced_questions(subject, num_multiple=2, num_numerical=2):
    """Generate multiple answer and numerical questions using Together AI."""
    prompt = f"""Generate {num_multiple} multiple answer questions and {num_numerical} numerical questions for {subject}.
Format each question as a JSON object with this structure for multiple answer questions:
{{
    "question": "Technical question text (keep it concise)",
    "options": ["option1", "option2", "option3", "option4"],
    "correct_answers": [0, 2],  // Array of correct option indices
    "explanation": "Brief 1-2 line explanation only",
    "type": "multiple_answer"
}}

And this structure for numerical questions:
{{
    "question": "Technical question text that requires a numerical answer (keep it concise)",
    "correct_answer": 42.5,  // The exact numerical answer
    "explanation": "Brief 1-2 line explanation only",
    "type": "numerical",
    "units": "units of measurement if applicable"
}}

Important:
1. Keep questions technically challenging but concise
2. Keep explanations very brief (1-2 lines maximum)
3. Return ONLY a valid JSON array containing the questions
4. No additional text or formatting
5. No long mathematical derivations in explanations"""

    try:
        response = together_client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical question generator for GATE exam questions. Generate concise questions with brief explanations (1-2 lines max). Return only valid JSON with no additional text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000,  # Reduced from 2000
            temperature=0.7
        )
        
        # Get the content and clean it
        content = response.choices[0].message.content.strip()
        
        # Remove any markdown code block indicators
        content = re.sub(r'^```json\s*|\s*```$', '', content, flags=re.MULTILINE)
        
        # Remove any potential comments
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        
        # Normalize newlines and remove extra whitespace
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        content = re.sub(r'\n\s*\n', '\n', content)  # Remove empty lines
        
        # Remove UTF-8 BOM if present
        content = content.encode('utf-8').decode('utf-8-sig')
        
        # Ensure content starts with [ and ends with ]
        content = content.strip()
        if not content.startswith('['):
            content = '[' + content
        if not content.endswith(']'):
            content = content + ']'
        
        try:
            # Parse the cleaned JSON
            questions = json.loads(content)
            
            # Ensure we have a list
            if not isinstance(questions, list):
                questions = [questions]
            
            # Validate and clean each question
            valid_questions = []
            for q in questions:
                # Truncate explanations if they're too long (max 150 chars)
                if 'explanation' in q:
                    q['explanation'] = q['explanation'][:150]
                
                # Ensure all required fields are present
                if q.get('type') == 'numerical':
                    if all(key in q for key in ['question', 'correct_answer', 'explanation', 'type']):
                        valid_questions.append(q)
                elif q.get('type') == 'multiple_answer':
                    if all(key in q for key in ['question', 'options', 'correct_answers', 'explanation', 'type']):
                        valid_questions.append(q)
            
            # Add subject to each question
            for q in valid_questions:
                q['subject'] = subject
            
            return valid_questions
            
        except json.JSONDecodeError as je:
            print(f"JSON parsing error for {subject}: {str(je)}")
            print("Cleaned content that failed to parse:", content)
            return []
            
    except Exception as e:
        print(f"Error generating advanced questions for {subject}: {str(e)}")
        return []

async def get_math_questions():
    """Get questions from Engineering Mathematics."""
    # Get 6 MCQ questions from database
    selected = await get_questions_from_db('Engineering Mathematics', 6)
    for q in selected:
        q['subject'] = 'Engineering Mathematics'
        q['type'] = 'single_answer'
    
    # Generate 4 advanced questions (2 multiple answer, 2 numerical)
    advanced_questions = generate_advanced_questions('Engineering Mathematics')
    
    return selected + advanced_questions

async def get_digital_logic_questions():
    """Get questions from Digital Logic."""
    # Get 4 MCQ questions from database
    selected = await get_questions_from_db('Digital Logic', 4)
    for q in selected:
        q['subject'] = 'Digital Logic'
        q['type'] = 'single_answer'
    
    # Generate 4 advanced questions
    advanced_questions = generate_advanced_questions('Digital Logic')
    
    return selected + advanced_questions

async def get_computer_networks_questions():
    """Get questions from Computer Networks."""
    # Get 4 MCQ questions from database
    selected = await get_questions_from_db('Computer Networks', 4)
    for q in selected:
        q['subject'] = 'Computer Networks'
        q['type'] = 'single_answer'
    
    # Generate 4 advanced questions
    advanced_questions = generate_advanced_questions('Computer Networks')
    
    return selected + advanced_questions

async def get_machine_learning_questions():
    """Get questions from Machine Learning."""
    # Get 4 MCQ questions from database
    selected = await get_questions_from_db('Machine Learning', 4)
    for q in selected:
        q['subject'] = 'Machine Learning'
        q['type'] = 'single_answer'
    
    # Generate 4 advanced questions
    advanced_questions = generate_advanced_questions('Machine Learning')
    
    return selected + advanced_questions

async def get_software_engineering_questions():
    """Get questions from Software Engineering."""
    # Get 4 MCQ questions from database
    selected = await get_questions_from_db('Software Engineering', 4)
    for q in selected:
        q['subject'] = 'Software Engineering'
        q['type'] = 'single_answer'
    
    # Generate 4 advanced questions
    advanced_questions = generate_advanced_questions('Software Engineering')
    
    return selected + advanced_questions

async def get_cloud_computing_questions():
    """Get questions from Cloud Computing."""
    # Get 3 MCQ questions from database
    selected = await get_questions_from_db('Cloud Computing', 3)
    for q in selected:
        q['subject'] = 'Cloud Computing'
        q['type'] = 'single_answer'
    
    # Generate 4 advanced questions
    advanced_questions = generate_advanced_questions('Cloud Computing')
    
    return selected + advanced_questions

async def get_cybersecurity_questions():
    """Get questions from Cybersecurity."""
    # Get 2 MCQ questions from database
    selected = await get_questions_from_db('Cybersecurity', 2)
    for q in selected:
        q['subject'] = 'Cybersecurity'
        q['type'] = 'single_answer'
    
    # Generate 4 advanced questions
    advanced_questions = generate_advanced_questions('Cybersecurity')
    
    return selected + advanced_questions

async def get_aptitude_questions():
    """Get questions for Aptitude and Reasoning."""
    # Get 10 MCQ questions from database
    selected = await get_questions_from_db('Aptitude and Reasoning', 10)
    for q in selected:
        q['subject'] = 'Aptitude and Reasoning'
        q['type'] = 'single_answer'
    return selected

def get_user_answer():
    """Get and validate user input for answers."""
    while True:
        try:
            answer = int(input("Your answer (1-4): "))
            if 1 <= answer <= 4:
                return answer - 1  # Convert to 0-based index
            print("Please enter a number between 1 and 4")
        except ValueError:
            print("Please enter a valid number")

async def main():
    """Main function to run the mock test."""
    # Get questions from each subject sequentially
    print("Fetching Aptitude and Reasoning questions...")
    aptitude_questions = await get_aptitude_questions()
    
    print("Fetching Engineering Mathematics questions...")
    math_questions = await get_math_questions()
    
    print("Fetching Digital Logic questions...")
    digital_questions = await get_digital_logic_questions()
    
    print("Fetching Computer Networks questions...")
    networks_questions = await get_computer_networks_questions()
    
    print("Fetching Machine Learning questions...")
    ml_questions = await get_machine_learning_questions()
    
    print("Fetching Software Engineering questions...")
    se_questions = await get_software_engineering_questions()
    
    print("Fetching Cloud Computing questions...")
    cloud_questions = await get_cloud_computing_questions()
    
    print("Fetching Cybersecurity questions...")
    security_questions = await get_cybersecurity_questions()
    
    # Combine all questions in desired order
    all_questions = (
        aptitude_questions +  # Aptitude first
        math_questions +      # Math second
        digital_questions +
        networks_questions +
        ml_questions +
        se_questions +
        cloud_questions +
        security_questions
    )
    
    # Start the quiz
    print("\n=== GATE Multi-Subject Quiz ===")
    print(f"Total Questions: {len(all_questions)} (2 from each subject)\n")
    
    user_answers = []
    for idx, question in enumerate(all_questions, start=1):
        print(f"\nQuestion {idx} [{question['subject']}]:")
        print(question['question'])
        for i, option in enumerate(question['options']):
            print(f"  {i + 1}. {option}")
        user_answers.append(get_user_answer())
    
    # Show results
    print("\n=== Quiz Results ===\n")
    correct_count = 0
    results_by_subject = {}
    
    for idx, (question, user_answer) in enumerate(zip(all_questions, user_answers), start=1):
        correct = user_answer == question['correct_answer']
        if correct:
            correct_count += 1
        
        # Initialize subject results if not exists
        subject = question['subject']
        if subject not in results_by_subject:
            results_by_subject[subject] = {'correct': 0, 'total': 0}
        results_by_subject[subject]['total'] += 1
        if correct:
            results_by_subject[subject]['correct'] += 1
        
        print(f"\nQuestion {idx} [{subject}]:")
        print(f"Your answer: Option {user_answer + 1}")
        print(f"Correct answer: Option {question['correct_answer'] + 1}")
        print(f"Status: {'✓ Correct' if correct else '✗ Wrong'}")
        print(f"Explanation: {question['explanation']}")
        print("-" * 50)
    
    # Show final score and subject-wise breakdown
    total_questions = len(all_questions)
    score_percentage = (correct_count / total_questions) * 100
    
    print("\n=== Score Breakdown ===")
    print("\nSubject-wise Performance:")
    for subject, results in results_by_subject.items():
        subject_percentage = (results['correct'] / results['total']) * 100
        print(f"{subject}: {results['correct']}/{results['total']} ({subject_percentage:.1f}%)")
    
    print(f"\nOverall Score: {correct_count}/{total_questions} ({score_percentage:.1f}%)")
    
    if score_percentage >= 70:
        print("\nExcellent! You've passed the quiz!")
    else:
        print("\nKeep practicing! Try to aim for 70% or higher.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())