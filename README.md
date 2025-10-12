# Google Minesweeper Solver v2.0

A refactored and optimized minesweeper solver with GUI interface, built with object-oriented design principles.

## Features

- **Unified Interface**: Single GUI application for all difficulty levels
- **Optimized Performance**: Eliminates redundant screenshots and OCR processing
- **Modular Architecture**: Clean separation of concerns with dedicated classes
- **Configurable**: All settings stored in `config.ini` file
- **Better Error Handling**: Comprehensive logging and error management
- **CAPTCHA Handling**: Automatic detection and human-assisted completion

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Tesseract OCR:
   - **macOS**: `brew install tesseract`
   - **Ubuntu/Debian**: `sudo apt install tesseract-ocr`
   - **Windows**: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)

3. Update tesseract path in `config.ini` if needed

## Usage

Run the application:
```bash
python main.py
```

Select your preferred difficulty level and click "Start Solver". The application will:
1. Open Google Minesweeper in your browser
2. Automatically select the chosen difficulty
3. Analyze the board and make safe moves
4. Continue until the game is solved or no more safe moves are available

## Architecture

### Directory Structure
```
MinesweeperSolver/
├── main.py                 # Entry point with GUI
├── config.ini              # Configuration file
├── requirements.txt        # Python dependencies
├── src/
│   ├── __init__.py
│   ├── board_analyzer.py   # BoardAnalyzer class
│   ├── game_controller.py  # GameController class
│   ├── solver.py           # MinesweeperSolver class
│   └── gui.py              # DifficultyGUI class
├── assets/                 # Images (WinReq.png, etc.)
└── temp/                   # Temporary screenshots
```

### Key Classes

- **`DifficultyGUI`**: Tkinter-based GUI for difficulty selection and control
- **`GameController`**: Manages browser automation and game execution
- **`BoardAnalyzer`**: Handles screenshot analysis, OCR, and change detection
- **`MinesweeperSolver`**: Implements the core solving logic

## Configuration

Edit `config.ini` to customize:
- Tesseract OCR path
- Grid dimensions for each difficulty
- Screen coordinates for board detection
- CAPTCHA timeout settings (default: 5 minutes)

## Improvements from v1.0

- ✅ Removed hardcoded values (tesseract path, grid dimensions)
- ✅ Eliminated redundant screenshots and OCR processing
- ✅ Implemented object-oriented design with proper separation of concerns
- ✅ Added comprehensive error handling and logging
- ✅ Created unified GUI interface
- ✅ Optimized coordinate calculations
- ✅ Added configuration file for easy customization
- ✅ Improved code maintainability and readability
- ✅ Added automatic CAPTCHA detection and human-assisted completion
- ✅ Robust element detection with multiple selector fallbacks

## Troubleshooting

1. **"Tesseract not found"**: Update the path in `config.ini`
2. **"Browser won't open"**: Ensure Chrome is installed and accessible
3. **"Incorrect board detection"**: Verify screen coordinates in `config.ini`
4. **"Game not starting"**: Check internet connection and Google Minesweeper accessibility
5. **"CAPTCHA appears"**: Complete the captcha manually in the browser window - the solver will wait automatically

## Logging

The application creates detailed logs in `minesweeper_solver.log` for debugging and monitoring.
