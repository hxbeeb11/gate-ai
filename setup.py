import subprocess
import sys
import os

def main():
    # Create virtual environment
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "venv"])
    
    # Activate virtual environment
    if sys.platform == "win32":
        pip_cmd = os.path.join("venv", "Scripts", "pip")
        python_cmd = os.path.join("venv", "Scripts", "python")
    else:
        pip_cmd = os.path.join("venv", "bin", "pip")
        python_cmd = os.path.join("venv", "bin", "python")
    
    # Install requirements
    print("Installing requirements...")
    subprocess.run([pip_cmd, "install", "-r", "requirements.txt"])
    
    # Download NLTK data using the virtual environment's Python
    print("Downloading NLTK data...")
    nltk_script = """
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
"""
    subprocess.run([python_cmd, "-c", nltk_script])
    
    # Create necessary directories
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/adaptive_state", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    
    print("\nSetup completed successfully!")
    print("\nTo get started:")
    if sys.platform == "win32":
        print("1. Run: .\\venv\\Scripts\\activate")
    else:
        print("1. Run: source venv/bin/activate")
    print("2. Run: python src/train_bert.py")
    print("3. Run: python src/app.py")
    print("\nThe web interface will be available at http://127.0.0.1:5000")

if __name__ == "__main__":
    main() 