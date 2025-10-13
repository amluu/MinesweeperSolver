# Google Minesweeper Solver v3.0

A Google Minesweeper Solver

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. **Run the application**:
```bash
python main.py
```
2. **Solve!**:
* change the difficulty to match your board and watch it run!

### Directory Structure
```
MinesweeperSolver/
├── main.py                 # Entry point with GUI
├── config.ini              # Configuration file
├── requirements.txt        # Python dependencies
├── README.md               # Documentation
├── src/                    # Source code modules
│   ├── board_detector.py   # Board detection and analysis
│   ├── csp_solver.py       # Constraint satisfaction problem solver
│   ├── deterministic_solver.py # Core solving logic
│   ├── game_controller.py  # Game interaction and control
│   ├── gui.py              # GUI interface
│   └── state_manager.py    # Game state tracking
```

### Key Classes

- **`GoogleMinesweeperGUI`**: Tkinter-based GUI for solver control
- **`MinesweeperSolver`**: Core deterministic solving logic
- **`MinesweeperCSPSolver`**: Constraint satisfaction problem solver for advanced deduction
- **`MinesweeperStateManager`**: Game state tracking and management
- **`GoogleMinesweeperDetector`**: Board detection and analysis
- **`GoogleMinesweeperController`**: Game interaction and control

## Tools & Technologies

### Computer Vision & Screen Capture
- **pyautogui**: Automated screen capture and mouse/keyboard control
- **mss**: High-performance screen capture for board detection
- **Pillow (PIL)**: Image processing and manipulation
- **OpenCV**: Computer vision for board analysis and cell detection
- **NumPy**: Numerical operations on image data

### Solving Algorithms

#### 1. Deterministic Logic
- **Basic Pattern Recognition**: Identifies obvious safe moves and mines
- **Neighbor Analysis**: Analyzes numbered cells and their surrounding cells
- **Constraint Satisfaction**: Determines mines based on number constraints

#### 2. Constraint Satisfaction Problem (CSP) Solver
- **OR-Tools**: Google's optimization library for advanced constraint solving
- **Multi-constraint Analysis**: Considers multiple numbered cells simultaneously
- **Probability Calculation**: Computes mine probabilities for uncertain situations

#### 3. Probabilistic Strategy
- **Risk Assessment**: Calculates safest moves when no certain moves exist
- **Probability-based Decision Making**: Chooses cells with lowest mine probability
- **Fallback Mechanism**: Enables continued solving when deterministic methods fail

### Game State Management
- **State Tracking**: Maintains internal representation of board state
- **Flag Management**: Tracks flagged mines for accurate constraint solving
- **Move History**: Prevents infinite loops and detects stuck states
- **Board Synchronization**: Merges OCR results with internal state

### Board Detection & Analysis
- **Pixel-perfect Detection**: Uses precise coordinates for Google Minesweeper
- **OCR Integration**: Reads numbers and board state from screenshots
- **Multi-difficulty Support**: Adapts to Easy (9x9), Medium (16x16), Hard (16x30)
- **Real-time Analysis**: Continuously monitors board changes during solving


