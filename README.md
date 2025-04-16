# Cash Tracker Application

A desktop application for tracking cash transactions and managing money transfers between users.

## Features

- User Authentication (Login/Register)
- Unique ID for each user
- Add/Remove Cash transactions
- Transfer money between users
- Transaction history with detailed view
- Real-time balance updates
- Secure password handling
- Modern and intuitive UI

## Technical Details

- Built with Python and PyQt5
- Uses SQLite for data storage
- Secure password hashing with Werkzeug
- Standalone executable with PyInstaller

## Installation

1. Install Python 3.11 or later
2. Create a virtual environment:
```bash
python -m venv venv
```
3. Activate the virtual environment:
   - Windows: `.\venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install required packages:
```bash
pip install -r requirements.txt
```

## Running the Application

### Development Mode
```bash
python desktop_app.py
```

### Build Executable
```bash
python build.py
```
The executable will be created in the `dist` folder.

## Security Features

- Password hashing using Werkzeug
- SQLite database for secure data storage
- Input validation and sanitization
- Secure money transfer system

## Upcoming Features

- Transaction categories
- Advanced analytics and reporting
- Budget planning tools
- Export functionality
- Favorite recipients
- QR code sharing
- Dark/Light theme
- And more!

## Contributing

Feel free to submit issues and enhancement requests! 