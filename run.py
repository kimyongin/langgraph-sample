import subprocess
import sys
import os
import logging

# Configure logging to show INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    """Run the collector application."""
    try:
        # Check if streamlit is installed
        try:
            import streamlit
        except ImportError:
            print("Streamlit is not installed. Installing required packages...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "langchain", "langgraph"])
            print("Packages installed successfully.")
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Add package to Python path
        sys.path.append(current_dir)
        
        # Run the Streamlit application
        streamlit_file = os.path.join(current_dir, "src", "app.py")
        print(f"Starting Streamlit application: {streamlit_file}")
        subprocess.run([sys.executable, "-m", "streamlit", "run", streamlit_file])
        
    except Exception as e:
        print(f"Error running the application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 