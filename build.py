import PyInstaller.__main__
import os
import sys

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define the icon path (you can add an icon later)
# icon_path = os.path.join(current_dir, 'icon.ico')

# Define PyInstaller arguments
args = [
    'desktop_app.py',  # Your main script
    '--name=CashTracker',  # Name of the executable
    '--onefile',  # Create a single executable
    '--windowed',  # Don't show console window
    '--clean',  # Clean PyInstaller cache
    '--add-data', f'{os.path.join(current_dir, "requirements.txt")};.',  # Include requirements.txt
    '--hidden-import=PyQt5',
    '--hidden-import=PyQt5.QtCore',
    '--hidden-import=PyQt5.QtGui',
    '--hidden-import=PyQt5.QtWidgets',
    '--hidden-import=werkzeug.security',
    '--hidden-import=sqlite3',
    '--noconfirm',  # Replace output directory without asking
    # '--icon', icon_path,  # Add icon (uncomment when you have an icon)
]

# Run PyInstaller
PyInstaller.__main__.run(args)

# Copy the database file to the dist directory if it exists
db_path = os.path.join(current_dir, 'cash_tracker.db')
dist_db_path = os.path.join(current_dir, 'dist', 'cash_tracker.db')
if os.path.exists(db_path):
    import shutil
    shutil.copy2(db_path, dist_db_path)
    print("Database file copied to dist directory.") 