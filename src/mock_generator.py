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

async def get_diagram_question_from_db(subject: str) -> list:
    """
    Fetch a random diagram question from database for a specific subject.
    Returns in the format appropriate for diagram questions.
    """
    try:
        # Query the diagram_questions table
        result = db.client.table('diagram_questions')\
            .select('*')\
            .eq('subject', subject)\
            .execute()
        
        if not result.data:
            print(f"Warning: No diagram questions found in database for {subject}")
            return []
            
        # Randomly select one question
        if len(result.data) > 0:
            selected_question = random.choice(result.data)
            
            # Format the question to match current structure
            diagram_question = {
                'question': selected_question['question'],
                'options': selected_question['options'],
                'correct_answer': selected_question['correct_answer'],
                'explanation': selected_question['explanation'],
                'svg_code': selected_question['svg_code'],
                'type': 'diagram_question',
                'subject': subject
            }
            
            print(f"Successfully fetched diagram question for {subject}")
            return [diagram_question]
        
        return []
        
    except Exception as e:
        print(f"Error fetching diagram question from database for {subject}: {str(e)}")
        return []

def generate_advanced_questions(subject, num_multiple=2, num_numerical=2, num_diagram=0):
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

def generate_diagram_questions(subject, count=1):
    """Generate diagram-based questions using a two-step approach."""
    if count <= 0:
        return []
    
    # Subject-specific diagram guidelines
    subject_guidelines = {
        "Digital Logic": """
- Logic circuit analysis (AND, OR, NOT, XOR gates)
- Sequential circuit behavior (flip-flops, latches)
- Karnaugh maps for boolean simplification
- State diagrams for finite state machines
- Timing diagrams showing signal transitions
""",
        "Computer Networks": """
- Network topologies (star, bus, ring, mesh)
- Protocol stack layers (OSI or TCP/IP model)
- Packet structure and headers
- Routing algorithms and path selection
- Subnetting and IP addressing schemes
""",
        "Machine Learning": """
- Decision tree structures
- Neural network architectures
- Clustering visualizations
- Support vector machine boundaries
- Confusion matrix representations
""",
        "Cloud Computing": """
- Cloud service models (IaaS, PaaS, SaaS)
- Virtualization architectures
- Container orchestration diagrams
- Distributed system architectures
- Load balancing configurations
"""
    }
    
    # Get the appropriate guidelines for this subject
    diagram_focus = subject_guidelines.get(subject, "")
    
    # Step 1: Generate questions that would benefit from diagrams
    question_prompt = f"""Generate {count} technical questions for {subject} that would benefit from having a diagram.
These should be questions where a visual diagram would help understand the problem.

For {subject}, focus on ONE of these topics (choose randomly):
{diagram_focus}

Format each question as a JSON object with this structure:
{{
    "question": "Technical question text that refers to a diagram (keep it concise)",
    "options": ["option1", "option2", "option3", "option4"],
    "correct_answer": 2,  // Index of correct option
    "explanation": "Brief 1-2 line explanation only",
    "diagram_description": "Detailed description of what diagram should show",
    "diagram_type": "Specific type of diagram (e.g., 'decision tree', 'network topology', etc.)"
}}

Important:
1. The question should explicitly refer to "the diagram" or "the figure shown"
2. The diagram_description should be detailed enough to create an accurate SVG
3. Return ONLY a valid JSON array containing the questions
4. No additional text or formatting
5. IMPORTANT: Be creative and vary the types of diagrams - don't always use the same diagram type"""

    try:
        # First generate the questions with diagram descriptions
        response = together_client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical question generator for GATE exam questions that require diagrams. Generate questions where a diagram would be essential for understanding. Be creative and vary the types of diagrams you create."
                },
                {
                    "role": "user",
                    "content": question_prompt
                }
            ],
            max_tokens=1000,
            temperature=0.8
        )
        
        # Get the content and clean it
        content = response.choices[0].message.content.strip()
        content = re.sub(r'^```json\s*|\s*```$', '', content, flags=re.MULTILINE)
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        content = re.sub(r'\n\s*\n', '\n', content)
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
            
            # Now generate SVG for each question
            diagram_questions = []
            
            for q in questions:
                if 'diagram_description' not in q:
                    continue
                
                # Subject-specific SVG examples - now providing multiple examples per subject
                svg_examples = {
"Digital Logic": """
Example 1 - Logic Gate Circuit:
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <title>Logic Gate Circuit Example</title>
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#000000" />
    </marker>
  </defs>
  <!-- Title -->
  <text x="400" y="60" text-anchor="middle" font-size="28" font-weight="bold">Simple Logic Circuit</text>
  
  <!-- Input labels -->
  <text x="100" y="180" text-anchor="end" font-size="24">A</text>
  <text x="100" y="300" text-anchor="end" font-size="24">B</text>
  <text x="100" y="420" text-anchor="end" font-size="24">C</text>
  
  <!-- Input lines -->
  <line x1="120" y1="180" x2="240" y2="180" stroke="#000000" stroke-width="2"/>
  <line x1="120" y1="300" x2="200" y2="300" stroke="#000000" stroke-width="2"/>
  <line x1="200" y1="300" x2="200" y2="220" stroke="#000000" stroke-width="2"/>
  <line x1="200" y1="220" x2="240" y2="220" stroke="#000000" stroke-width="2"/>
  <line x1="120" y1="420" x2="240" y2="420" stroke="#000000" stroke-width="2"/>
  
  <!-- AND Gate -->
  <path d="M240,160 Q300,160 300,200 Q300,240 240,240 Z" fill="#FFFFFF" stroke="#000000" stroke-width="2"/>
  <text x="270" y="200" text-anchor="middle" dominant-baseline="middle" font-size="24">AND</text>
  
  <!-- OR Gate -->
  <path d="M240,380 Q270,380 300,400 Q270,420 240,420 Q270,400 240,380 Z" fill="#FFFFFF" stroke="#000000" stroke-width="2"/>
  <text x="270" y="400" text-anchor="middle" dominant-baseline="middle" font-size="24">OR</text>
  
  <!-- Connecting lines -->
  <line x1="300" y1="200" x2="380" y2="200" stroke="#000000" stroke-width="2"/>
  <line x1="300" y1="400" x2="380" y2="400" stroke="#000000" stroke-width="2"/>
  <line x1="380" y1="200" x2="380" y2="280" stroke="#000000" stroke-width="2"/>
  <line x1="380" y1="400" x2="380" y2="320" stroke="#000000" stroke-width="2"/>
  
  <!-- NOT Gate (inverter) -->
  <path d="M380,280 L440,300 L380,320 Z" fill="#FFFFFF" stroke="#000000" stroke-width="2"/>
  <circle cx="450" cy="300" r="10" fill="#FFFFFF" stroke="#000000" stroke-width="2"/>
  
  <!-- Output line -->
  <line x1="460" y1="300" x2="560" y2="300" stroke="#000000" stroke-width="2" marker-end="url(#arrowhead)"/>
  
  <!-- Output label -->
  <text x="580" y="300" font-size="24">Output</text>
</svg>

Example 2 - State Diagram:
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <title>State Diagram Example</title>
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#000000" />
    </marker>
  </defs>
  <!-- Title -->
  <text x="400" y="60" text-anchor="middle" font-size="28" font-weight="bold">Finite State Machine</text>
  
  <!-- States -->
  <circle cx="200" cy="200" r="60" fill="#FFFFFF" stroke="#000000" stroke-width="2"/>
  <text x="200" y="200" text-anchor="middle" dominant-baseline="middle" font-size="24">S0</text>
  <text x="200" y="230" text-anchor="middle" dominant-baseline="middle" font-size="18">Idle</text>
  
  <circle cx="400" cy="400" r="60" fill="#FFFFFF" stroke="#000000" stroke-width="2"/>
  <text x="400" y="400" text-anchor="middle" dominant-baseline="middle" font-size="24">S1</text>
  <text x="400" y="430" text-anchor="middle" dominant-baseline="middle" font-size="18">Processing</text>
  
  <circle cx="600" cy="200" r="60" fill="#FFFFFF" stroke="#000000" stroke-width="2"/>
  <text x="600" y="200" text-anchor="middle" dominant-baseline="middle" font-size="24">S2</text>
  <text x="600" y="230" text-anchor="middle" dominant-baseline="middle" font-size="18">Done</text>
  
  <!-- Transitions -->
  <path d="M250 230 C 300 300, 350 350, 350 400" stroke="#000000" stroke-width="2" fill="none" marker-end="url(#arrowhead)"/>
  <text x="280" y="320" text-anchor="middle" font-size="18">Start=1</text>
  
  <path d="M450 370 C 500 300, 550 250, 550 200" stroke="#000000" stroke-width="2" fill="none" marker-end="url(#arrowhead)"/>
  <text x="520" y="320" text-anchor="middle" font-size="18">Done=1</text>
  
  <path d="M600 140 C 600 100, 200 100, 200 140" stroke="#000000" stroke-width="2" fill="none" marker-end="url(#arrowhead)"/>
  <text x="400" y="120" text-anchor="middle" font-size="18">Reset=1</text>
</svg>

Example 3 - Timing Diagram:
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <title>Timing Diagram Example</title>
  <!-- Title -->
  <text x="400" y="60" text-anchor="middle" font-size="28" font-weight="bold">Digital Timing Diagram</text>
  
  <!-- Time axis -->
  <line x1="100" y1="500" x2="700" y2="500" stroke="#000000" stroke-width="2"/>
  <text x="400" y="530" text-anchor="middle" font-size="20">Time</text>
  
  <!-- Time markers -->
  <line x1="100" y1="500" x2="100" y2="510" stroke="#000000" stroke-width="2"/>
  <text x="100" y="530" text-anchor="middle" font-size="16">0</text>
  <line x1="200" y1="500" x2="200" y2="510" stroke="#000000" stroke-width="2"/>
  <text x="200" y="530" text-anchor="middle" font-size="16">1</text>
  <line x1="300" y1="500" x2="300" y2="510" stroke="#000000" stroke-width="2"/>
  <text x="300" y="530" text-anchor="middle" font-size="16">2</text>
  <line x1="400" y1="500" x2="400" y2="510" stroke="#000000" stroke-width="2"/>
  <text x="400" y="530" text-anchor="middle" font-size="16">3</text>
  <line x1="500" y1="500" x2="500" y2="510" stroke="#000000" stroke-width="2"/>
  <text x="500" y="530" text-anchor="middle" font-size="16">4</text>
  <line x1="600" y1="500" x2="600" y2="510" stroke="#000000" stroke-width="2"/>
  <text x="600" y="530" text-anchor="middle" font-size="16">5</text>
  <line x1="700" y1="500" x2="700" y2="510" stroke="#000000" stroke-width="2"/>
  <text x="700" y="530" text-anchor="middle" font-size="16">6</text>
  
  <!-- Signal labels -->
  <text x="80" y="150" text-anchor="end" font-size="20">Clock</text>
  <text x="80" y="250" text-anchor="end" font-size="20">Data</text>
  <text x="80" y="350" text-anchor="end" font-size="20">Enable</text>
  <text x="80" y="450" text-anchor="end" font-size="20">Output</text>
  
  <!-- Clock signal -->
  <polyline points="100,150 100,100 150,100 150,150 200,150 200,100 250,100 250,150 300,150 300,100 350,100 350,150 400,150 400,100 450,100 450,150 500,150 500,100 550,100 550,150 600,150 600,100 650,100 650,150 700,150" 
            fill="none" stroke="#000000" stroke-width="2"/>
  
  <!-- Data signal -->
  <polyline points="100,250 100,200 200,200 200,250 400,250 400,200 700,200" 
            fill="none" stroke="#000000" stroke-width="2"/>
  
  <!-- Enable signal -->
  <polyline points="100,350 100,350 300,350 300,300 500,300 500,350 700,350" 
            fill="none" stroke="#000000" stroke-width="2"/>
  
  <!-- Output signal -->
  <polyline points="100,450 100,450 350,450 350,400 550,400 550,450 700,450" 
            fill="none" stroke="#000000" stroke-width="2"/>
</svg>
""",
                    "Computer Networks": """
Example 1 - Network node:
<rect x="200" y="200" width="160" height="80" rx="10" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>
<text x="280" y="240" text-anchor="middle" dominant-baseline="middle" font-size="24">Router</text>

Example 2 - Network topology:
<circle cx="400" cy="200" r="30" fill="#FFFFFF" stroke="#000000" stroke-width="2"></circle>
<circle cx="300" cy="300" r="30" fill="#FFFFFF" stroke="#000000" stroke-width="2"></circle>
<circle cx="500" cy="300" r="30" fill="#FFFFFF" stroke="#000000" stroke-width="2"></circle>
<line x1="400" y1="200" x2="300" y2="300" stroke="#000000" stroke-width="2"></line>
<line x1="400" y1="200" x2="500" y2="300" stroke="#000000" stroke-width="2"></line>

Example 3 - Protocol stack:
<rect x="200" y="200" width="200" height="60" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>
<rect x="200" y="260" width="200" height="60" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>
<rect x="200" y="320" width="200" height="60" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>
<text x="300" y="230" text-anchor="middle" dominant-baseline="middle" font-size="24">Application</text>
<text x="300" y="290" text-anchor="middle" dominant-baseline="middle" font-size="24">Transport</text>
<text x="300" y="350" text-anchor="middle" dominant-baseline="middle" font-size="24">Network</text>
""",
                    "Machine Learning": """
Example 1 - Decision tree:
<rect x="300" y="100" width="200" height="80" rx="10" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>
<text x="400" y="140" text-anchor="middle" dominant-baseline="middle" font-size="24">Feature X > 0.5</text>
<line x1="300" y1="180" x2="200" y2="260" stroke="#000000" stroke-width="2"></line>
<line x1="500" y1="180" x2="600" y2="260" stroke="#000000" stroke-width="2"></line>
<rect x="100" y="260" width="200" height="80" rx="10" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>
<rect x="500" y="260" width="200" height="80" rx="10" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>

Example 2 - Neural network:
<circle cx="200" cy="200" r="30" fill="#FFFFFF" stroke="#000000" stroke-width="2"></circle>
<circle cx="200" cy="300" r="30" fill="#FFFFFF" stroke="#000000" stroke-width="2"></circle>
<circle cx="200" cy="400" r="30" fill="#FFFFFF" stroke="#000000" stroke-width="2"></circle>
<circle cx="400" cy="250" r="30" fill="#FFFFFF" stroke="#000000" stroke-width="2"></circle>
<circle cx="400" cy="350" r="30" fill="#FFFFFF" stroke="#000000" stroke-width="2"></circle>
<circle cx="600" cy="300" r="30" fill="#FFFFFF" stroke="#000000" stroke-width="2"></circle>

Example 3 - Confusion matrix:
<rect x="200" y="200" width="100" height="100" fill="#E6F7FF" stroke="#000000" stroke-width="2"></rect>
<rect x="300" y="200" width="100" height="100" fill="#FFEBE6" stroke="#000000" stroke-width="2"></rect>
<rect x="200" y="300" width="100" height="100" fill="#FFEBE6" stroke="#000000" stroke-width="2"></rect>
<rect x="300" y="300" width="100" height="100" fill="#E6F7FF" stroke="#000000" stroke-width="2"></rect>
<text x="250" y="250" text-anchor="middle" dominant-baseline="middle" font-size="24">TP</text>
<text x="350" y="250" text-anchor="middle" dominant-baseline="middle" font-size="24">FP</text>
<text x="250" y="350" text-anchor="middle" dominant-baseline="middle" font-size="24">FN</text>
<text x="350" y="350" text-anchor="middle" dominant-baseline="middle" font-size="24">TN</text>
""",
                    "Cloud Computing": """
Example 1 - Cloud service:
<path d="M200,200 Q240,160 280,200 Q320,160 360,200 Q400,240 360,280 Q320,320 280,280 Q240,320 200,280 Q160,240 200,200" fill="#FFFFFF" stroke="#000000" stroke-width="2"></path>
<text x="280" y="240" text-anchor="middle" dominant-baseline="middle" font-size="24">Cloud Service</text>

Example 2 - Service architecture:
<rect x="100" y="200" width="160" height="80" rx="10" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>
<rect x="400" y="200" width="160" height="80" rx="10" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>
<rect x="700" y="200" width="160" height="80" rx="10" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>
<line x1="260" y1="240" x2="400" y2="240" stroke="#000000" stroke-width="2" marker-end="url(#arrowhead)"></line>
<line x1="560" y1="240" x2="700" y2="240" stroke="#000000" stroke-width="2" marker-end="url(#arrowhead)"></line>

Example 3 - Container orchestration:
<rect x="200" y="100" width="400" height="300" rx="10" fill="#F8F8F8" stroke="#000000" stroke-width="2"></rect>
<rect x="240" y="160" width="140" height="80" rx="10" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>
<rect x="420" y="160" width="140" height="80" rx="10" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>
<rect x="240" y="280" width="140" height="80" rx="10" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>
<rect x="420" y="280" width="140" height="80" rx="10" fill="#FFFFFF" stroke="#000000" stroke-width="2"></rect>
<text x="400" y="130" text-anchor="middle" dominant-baseline="middle" font-size="24">Kubernetes Cluster</text>
"""
                }
                
                # Get the appropriate example for this subject
                svg_example = svg_examples.get(subject, "")
                
                # Step 2: Generate SVG based on the diagram description
                svg_prompt = f"""Create an SVG diagram based on this description for a {subject} question:

"{q['diagram_description']}"

The diagram should:
1. Be clear, simple, and focused on the key elements
2. Use standard SVG elements (rect, circle, line, path, text)
3. Be 800px wide and 600px tall - USE THE FULL CANVAS SPACE
4. Scale your coordinates to use the entire available space (0,0 to 800,600)
5. Use appropriate colors and labels
6. Be directly embeddable in HTML

Important SVG guidelines:
- Use the full canvas width (800px) and height (600px) effectively
- Scale your elements appropriately for the larger canvas
- Center text labels inside shapes using text-anchor="middle" dominant-baseline="middle"
- For text inside shapes, use: <text x="[center-x]" y="[center-y]" text-anchor="middle" dominant-baseline="middle">Label</text>
- Add a 2px stroke to all shapes for better visibility at larger scale
- Use clear, contrasting colors
- Include a title element for accessibility

For {subject} diagrams, here are some examples of properly formatted elements:
```
{svg_example}
```

IMPORTANT: 
- Be creative and don't just copy the examples
- Create a diagram that best illustrates the specific concept described
- Use the FULL 800x600 canvas space - don't cluster elements in a small area
- Scale your coordinates appropriately (multiply typical coordinates by 2 for the larger canvas)
Return ONLY the SVG code with no additional text or explanation."""

                svg_response = together_client.chat.completions.create(
                    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an SVG diagram generator. Create clear, accurate SVG diagrams for technical questions. Return only valid SVG code with no additional text. Be creative and vary your diagram designs based on the specific concept being illustrated."
                        },
                        {
                            "role": "user",
                            "content": svg_prompt
                        }
                    ],
                    max_tokens=1500,
                    temperature=0.3
                )
                
                svg_content = svg_response.choices[0].message.content.strip()
                svg_content = re.sub(r'^```(?:svg|xml|html)?\s*|\s*```$', '', svg_content, flags=re.MULTILINE)
                
                # Additional SVG validation and sanitization
                # Ensure it has proper SVG tags
                if not svg_content.startswith('<svg'):
                    svg_content = f'<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">\n{svg_content}\n</svg>'
                
                # Ensure it has proper width and height
                if 'width=' not in svg_content or 'height=' not in svg_content:
                    svg_content = svg_content.replace('<svg', '<svg width="800" height="600"')
                
                # Ensure it has xmlns attribute
                if 'xmlns=' not in svg_content:
                    svg_content = svg_content.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')
                
                # Validate that we have SVG content
                if '<svg' in svg_content and '</svg>' in svg_content:
                    # Create the final question object
                    diagram_question = {
                        "question": q['question'],
                        "options": q['options'],
                        "correct_answer": q['correct_answer'],
                        "explanation": q['explanation'][:150],  # Truncate if too long
                        "svg_code": svg_content,
                        "type": "diagram_question",
                        "subject": subject
                    }
                    diagram_questions.append(diagram_question)
            
            return diagram_questions
            
        except json.JSONDecodeError as je:
            print(f"JSON parsing error for diagram questions: {str(je)}")
            return []
            
    except Exception as e:
        print(f"Error generating diagram questions for {subject}: {str(e)}")
        return []

async def get_math_questions():
    """Get questions from Engineering Mathematics."""
    # Get 7 MCQ questions from database
    selected = await get_questions_from_db('Engineering Mathematics', 7)
    for q in selected:
        q['subject'] = 'Engineering Mathematics'
        q['type'] = 'single_answer'
    
    # Generate 4 advanced questions (2 multiple answer, 2 numerical)
    advanced_questions = generate_advanced_questions('Engineering Mathematics')
    
    return selected + advanced_questions

async def get_digital_logic_questions():
    """Get questions from Digital Logic."""
    # Get 5 MCQ questions from database
    selected = await get_questions_from_db('Digital Logic', 5)
    for q in selected:
        q['subject'] = 'Digital Logic'
        q['type'] = 'single_answer'
    
    # Generate 4 advanced questions (2 multiple answer, 2 numerical)
    advanced_questions = generate_advanced_questions('Digital Logic', num_multiple=2, num_numerical=2)
    
    # Get 1 diagram question from database
    diagram_questions = await get_diagram_question_from_db('Digital Logic')
    
    return selected + advanced_questions + diagram_questions

async def get_computer_networks_questions():
    """Get questions from Computer Networks."""
    # Get 4 MCQ questions from database
    selected = await get_questions_from_db('Computer Networks', 4)
    for q in selected:
        q['subject'] = 'Computer Networks'
        q['type'] = 'single_answer'
    
    # Generate 4 advanced questions (2 multiple answer, 2 numerical)
    advanced_questions = generate_advanced_questions('Computer Networks', num_multiple=2, num_numerical=2)
    
    # Get 1 diagram question from database
    diagram_questions = await get_diagram_question_from_db('Computer Networks')
    
    return selected + advanced_questions + diagram_questions

async def get_machine_learning_questions():
    """Get questions from Machine Learning."""
    # Get 3 MCQ questions from database
    selected = await get_questions_from_db('Machine Learning', 3)
    for q in selected:
        q['subject'] = 'Machine Learning'
        q['type'] = 'single_answer'
    
    # Generate 3 advanced questions (2 multiple answer, 1 numerical)
    advanced_questions = generate_advanced_questions('Machine Learning', num_multiple=2, num_numerical=1)
    
    # Get 1 diagram question from database
    diagram_questions = await get_diagram_question_from_db('Machine Learning')
    
    return selected + advanced_questions + diagram_questions

async def get_software_engineering_questions():
    """Get questions from Software Engineering."""
    # Get 3 MCQ questions from database
    selected = await get_questions_from_db('Software Engineering', 3)
    for q in selected:
        q['subject'] = 'Software Engineering'
        q['type'] = 'single_answer'
    
    # Generate 3 advanced questions (2 multiple answer, 1 numerical)
    advanced_questions = generate_advanced_questions('Software Engineering', num_multiple=2, num_numerical=1)
    
    return selected + advanced_questions

async def get_cloud_computing_questions():
    """Get questions from Cloud Computing."""
    # Get 3 MCQ questions from database
    selected = await get_questions_from_db('Cloud Computing', 3)
    for q in selected:
        q['subject'] = 'Cloud Computing'
        q['type'] = 'single_answer'
    
    # Generate 3 advanced questions (2 multiple answer, 1 numerical)
    advanced_questions = generate_advanced_questions('Cloud Computing', num_multiple=2, num_numerical=1)
    
    # Get 1 diagram question from database
    diagram_questions = await get_diagram_question_from_db('Cloud Computing')
    
    return selected + advanced_questions + diagram_questions

async def get_cybersecurity_questions():
    """Get questions from Cybersecurity."""
    # Get 2 MCQ questions from database
    selected = await get_questions_from_db('Cybersecurity', 2)
    for q in selected:
        q['subject'] = 'Cybersecurity'
        q['type'] = 'single_answer'
    
    # Generate 3 advanced questions (2 multiple answer, 1 numerical)
    advanced_questions = generate_advanced_questions('Cybersecurity', num_multiple=2, num_numerical=1)
    
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
    print(f"Total Questions: {len(all_questions)}\n")
    
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