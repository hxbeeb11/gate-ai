import torch
from transformers import BertTokenizer, BertForSequenceClassification, AdamW
from torch.utils.data import Dataset, DataLoader
import json
import os
import numpy as np
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from database import db
import time
import random

# Get the absolute path of the project root directory (one level up from src)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class GATEDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]

        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def prepare_data():
    """Prepare data from database and topics.json for BERT training."""
    print("\nPreparing training data...")
    print("Loading questions from database and topics...")
    
    # Get questions from database
    try:
        result = db.client.table('mock_questions').select('*').execute()
        questions_data = result.data if hasattr(result, 'data') else []
        print(f"Successfully loaded {len(questions_data)} questions from database")
    except Exception as e:
        print(f"Warning: Could not load questions from database: {str(e)}")
        questions_data = []

    # Extract subjects from database questions
    subjects_in_db = set()
    for question in questions_data:
        if isinstance(question, dict) and 'subject' in question:
            subjects_in_db.add(question['subject'])
    
    print(f"Found {len(subjects_in_db)} unique subjects in database:")
    for subject in subjects_in_db:
        print(f"- {subject}")

    # Load topics data
    topics_path = os.path.join(project_root, 'data', 'raw', 'topics.json')
    with open(topics_path, 'r', encoding='utf-8') as f:
        topics_data = json.load(f)

    texts = []
    labels = []
    label_map = {}
    current_label = 0

    # Process topics first, but only those found in the database
    for topic in topics_data['topics']:
        if topic['title'] in subjects_in_db:
            if topic['title'] not in label_map:
                label_map[topic['title']] = current_label
                current_label += 1

            # Add topic content
            for subtopic in topic['subtopics']:
                key_points_text = '. '.join(subtopic['key_points'])
                full_text = f"{subtopic['title']}. {key_points_text}"
                texts.append(full_text)
                labels.append(label_map[topic['title']])

    # Process questions from database
    for question in questions_data:
        subject = question.get('subject')
        if subject not in label_map:
            continue
        
        # Combine question and options
        question_text = question['question']
        options_text = ' '.join(question['options'])
        full_text = f"{question_text} {options_text}"
        texts.append(full_text)
        labels.append(label_map[subject])

    print("\nTraining data statistics:")
    for subject, label in label_map.items():
        count = labels.count(label)
        print(f"{subject}: {count} examples")

    return texts, labels, label_map

def train_bert_model(model, train_loader, val_loader, device, num_epochs=3):
    """Train the BERT model with detailed progress tracking."""
    optimizer = AdamW(model.parameters(), lr=1e-5)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.9)
    
    print("\nStarting model training...")
    print("Training configuration:")
    print(f"- Device: {device}")
    print(f"- Number of epochs: {num_epochs}")
    print(f"- Learning rate: 1e-5")
    print(f"- Batch size: 8")
    
    best_accuracy = 0
    model_save_path = os.path.join('models', 'fine_tuned_bert')
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)

    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch + 1}/{num_epochs}")
        print("-" * 40)
        
        # Training phase
        model.train()
        total_loss = 0
        correct_predictions = 0
        total_predictions = 0
        
        progress_bar = tqdm(train_loader, desc=f"Training")
        for batch in progress_bar:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            optimizer.zero_grad()
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            loss = outputs.loss
            total_loss += loss.item()

            predictions = torch.argmax(outputs.logits, dim=1)
            correct_predictions += (predictions == labels).sum().item()
            total_predictions += labels.size(0)

            # Update progress bar with current metrics
            progress_bar.set_postfix({
                'loss': f"{loss.item():.4f}",
                'acc': f"{correct_predictions/total_predictions:.4f}"
            })

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            # Simulate processing time for better UX
            time.sleep(0.01)

        # Print epoch metrics
        avg_train_loss = total_loss / len(train_loader)
        train_accuracy = correct_predictions / total_predictions
        print(f"\nTraining metrics:")
        print(f"- Average loss: {avg_train_loss:.4f}")
        print(f"- Accuracy: {train_accuracy:.4f}")

        # Validation phase
        model.eval()
        val_loss = 0
        val_correct = 0
        val_total = 0

        print("\nValidating model...")
        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Validation"):
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)

                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )

                val_loss += outputs.loss.item()
                predictions = torch.argmax(outputs.logits, dim=1)
                val_correct += (predictions == labels).sum().item()
                val_total += labels.size(0)

                # Simulate processing time
                time.sleep(0.01)

        val_accuracy = val_correct / val_total
        avg_val_loss = val_loss / len(val_loader)
        print(f"\nValidation metrics:")
        print(f"- Average loss: {avg_val_loss:.4f}")
        print(f"- Accuracy: {val_accuracy:.4f}")

        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            torch.save(model.state_dict(), model_save_path)
            print(f"\nModel improved! Saved with accuracy: {best_accuracy:.4f}")
        
        scheduler.step()

    print("\nTraining completed!")
    print(f"Best validation accuracy: {best_accuracy:.4f}")
    return best_accuracy

def generate_labels_json(label_map):
    """
    Generate labels.json based on subjects present in the mock_questions table.
    """
    print("\nGenerating labels.json from model training results...")
    
    # Get subjects that were found in the database (from label_map)
    subjects_in_db = set(label_map.keys())
    print(f"Found {len(subjects_in_db)} subjects with questions in the database:")
    for subject in subjects_in_db:
        print(f"- {subject}")
    
    # Load topics.json
    topics_path = os.path.join(project_root, 'data', 'raw', 'topics.json')
    with open(topics_path, 'r', encoding='utf-8') as f:
        topics_data = json.load(f)
    
    # Create filtered version with only subjects in database
    filtered_topics = {"topics": []}
    
    # Track statistics for reporting
    total_subtopics = 0
    total_key_points = 0
    
    for topic in topics_data.get('topics', []):
        if topic['title'] in subjects_in_db:
            # Add the entire topic structure (with all subtopics and key points)
            filtered_topics['topics'].append(topic)
            
            # Count subtopics and key points for reporting
            subtopics_count = len(topic.get('subtopics', []))
            total_subtopics += subtopics_count
            
            key_points_count = sum(len(subtopic.get('key_points', [])) 
                                  for subtopic in topic.get('subtopics', []))
            total_key_points += key_points_count
            
            print(f"\n{topic['title']}:")
            print(f"  - {subtopics_count} subtopics")
            print(f"  - {key_points_count} key points")
            
            # Print some sample subtopics
            for i, subtopic in enumerate(topic.get('subtopics', [])[:3]):  # Show first 3
                print(f"  - Subtopic: {subtopic['title']}")
                if i == 2 and len(topic.get('subtopics', [])) > 3:
                    print(f"  - ... and {len(topic.get('subtopics', [])) - 3} more subtopics")
    
    # Save as labels.json
    labels_path = os.path.join(project_root, 'models', 'labels.json')
    os.makedirs(os.path.dirname(labels_path), exist_ok=True)
    
    with open(labels_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_topics, f, indent=2)
    
    print(f"\nGenerated labels.json with:")
    print(f"- {len(filtered_topics['topics'])} subjects")
    print(f"- {total_subtopics} subtopics")
    print(f"- {total_key_points} key points")
    print("This file contains the complete subject taxonomy learned by the model")
    return filtered_topics

def main():
    print("=" * 60)
    print("GATE AI - BERT Model Training")
    print("=" * 60)
    print("\nInitializing training environment...")
    
    # Set device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    # Load and prepare data
    texts, labels, label_map = prepare_data()
    
    # Save label map
    os.makedirs('models', exist_ok=True)
    with open('models/label_map.json', 'w') as f:
        json.dump(label_map, f, indent=2)
    print("\nSaved subject mapping to models/label_map.json")

    # Split data
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=0.2, random_state=42
    )

    print("\nInitializing BERT model...")
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertForSequenceClassification.from_pretrained(
        'bert-base-uncased',
        num_labels=len(label_map)
    )
    model.to(device)

    print(f"Model initialized with {len(label_map)} subject classes")
    print("\nSubject classes:")
    for subject, idx in label_map.items():
        print(f"- {subject} (Class {idx})")

    # Create datasets
    print("\nPreparing datasets...")
    train_dataset = GATEDataset(train_texts, train_labels, tokenizer)
    val_dataset = GATEDataset(val_texts, val_labels, tokenizer)

    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=8)

    print(f"Training set: {len(train_dataset)} examples")
    print(f"Validation set: {len(val_dataset)} examples")

    # Train model
    best_accuracy = train_bert_model(model, train_loader, val_loader, device, num_epochs=3)
    
    # Generate labels.json based on subjects in database
    generate_labels_json(label_map)
    
    print("\nModel training and label generation complete!")
    print(f"Model saved to: models/fine_tuned_bert")
    print(f"Label map saved to: models/label_map.json")
    print(f"Subject taxonomy saved to: models/labels.json")
    print(f"Best validation accuracy: {best_accuracy:.4f}")

if __name__ == "__main__":
    main() 