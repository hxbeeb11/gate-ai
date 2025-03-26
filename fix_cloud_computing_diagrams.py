#!/usr/bin/env python3

# Read the original JSON file
with open('data/processed/diagrams/digital_logic_diagram_questions.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Create a new version with the SVG code fixed
# Replace all occurrences of \" in SVG code with regular "
new_content = content.replace('\\"', '"')

# Write to a new file
with open('data/processed/diagrams/digital_logic_diagram_questions_fixed.json', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Created fixed version of cloud computing diagram questions") 