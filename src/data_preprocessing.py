import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import json
import os

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

class DataPreprocessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
    def preprocess_text(self, text):
        """
        Preprocess the input text by performing tokenization, lowercasing,
        stop word removal, and lemmatization.
        """
        # Lowercase the text
        text = text.lower()
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stop words and lemmatize
        tokens = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token not in self.stop_words and token.isalnum()
        ]
        
        return ' '.join(tokens)
    
    def process_raw_data(self, input_file, output_file):
        """
        Process raw data from input file and save cleaned data to output file.
        """
        # Read the input file
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
        elif input_file.endswith('.json'):
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                df = pd.json_normalize(data)
        else:
            raise ValueError("Unsupported file format. Use CSV or JSON.")
        
        # Process text columns
        text_columns = df.select_dtypes(include=['object']).columns
        for col in text_columns:
            df[f'processed_{col}'] = df[col].apply(self.preprocess_text)
        
        # Save processed data
        if output_file.endswith('.csv'):
            df.to_csv(output_file, index=False)
        elif output_file.endswith('.json'):
            df.to_json(output_file, orient='records', indent=2)
        else:
            raise ValueError("Unsupported output format. Use CSV or JSON.")
        
        return df

def main():
    # Initialize preprocessor
    preprocessor = DataPreprocessor()
    
    # Define input and output paths
    raw_dir = os.path.join('data', 'raw')
    processed_dir = os.path.join('data', 'processed')
    
    # Create processed directory if it doesn't exist
    os.makedirs(processed_dir, exist_ok=True)
    
    # Process all files in raw directory
    for filename in os.listdir(raw_dir):
        if filename.endswith(('.csv', '.json')):
            input_path = os.path.join(raw_dir, filename)
            output_path = os.path.join(processed_dir, f'processed_{filename}')
            
            print(f"Processing {filename}...")
            preprocessor.process_raw_data(input_path, output_path)
            print(f"Saved processed data to {output_path}")

if __name__ == "__main__":
    main() 