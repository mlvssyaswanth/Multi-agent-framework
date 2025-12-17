# Create a virtual environment - creates an isolated Python environment for the project
python3 -m venv venv || python -m venv venv
# Activate the virtual environment - activates the isolated environment
source venv/bin/activate
# Check pip version - displays the current pip version installed
pip --version
# Upgrade pip to the latest version - ensures pip is up to date for package installation
pip install --upgrade pip
# Install requirements from requirements.txt - installs all project dependencies
pip install -r requirements.txt
# Run the Streamlit application - starts the multi-agent coding framework web interface
streamlit run app.py