import configparser
import time
from typing import Tuple, List
import pyautogui

class GoogleMinesweeperController:
    """Game controller for Google Minesweeper using hardcoded coordinates."""
    
    def __init__(self, config_path: str = "config.ini"):
        """Initialize the controller with configuration."""
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.detector = None
        
        # Configure pyautogui for faster execution
        pyautogui.FAILSAFE = True  # Move mouse to corner to stop
        pyautogui.PAUSE = 0.01  # Minimal pause between actions for speed
        
    def set_detector(self, detector):
        """Set the board detector for coordinate calculation."""
        self.detector = detector
    
    def select_tab(self):
        """Click center of board to focus the Minesweeper tab."""
        if not self.detector:
            raise RuntimeError("Detector not set. Call set_detector() first.")
        
        if not self.detector.board_config:
            raise RuntimeError("Board config not set. Call set_difficulty() first.")
        
        # Calculate center of board
        board_config = self.detector.board_config
        center_x = board_config['x'] + (board_config['width'] // 2)
        center_y = board_config['y'] + (board_config['height'] // 2)
        
        pyautogui.click(center_x, center_y)
        time.sleep(0.1)  # Reduced wait for focus
    
    def set_difficulty(self, difficulty: str):
        """Set the game difficulty - user must manually select difficulty."""
        if difficulty not in ['easy', 'medium', 'hard']:
            raise ValueError(f"Invalid difficulty: {difficulty}")
        
        
        # No longer clicking dropdown - user must select difficulty manually
        # This ensures the first click is always the center click, not dropdown clicks
    
    def click_cell(self, row: int, col: int, button: str = 'left', focus_tab: bool = True):
        """Click a specific cell on the board."""
        if not self.detector:
            raise RuntimeError("Detector not set. Call set_detector() first.")
        
        # Only focus tab if explicitly requested (for batching)
        if focus_tab:
            self.select_tab()
        
        # Get cell coordinates from detector
        x, y = self.detector.get_cell_coordinates(row, col)
        
        
        # Get current screen size for validation
        screen_width, screen_height = pyautogui.size()
        
        # Validate coordinates are within screen bounds
        if x < 0 or x >= screen_width or y < 0 or y >= screen_height:
            return
        
        # Move mouse to coordinates quickly and click
        pyautogui.moveTo(x, y, duration=0.1)  # Much faster movement
        
        # Click the cell
        if button == 'left':
            pyautogui.click(x, y)
        elif button == 'right':
            pyautogui.rightClick(x, y)
        else:
            raise ValueError(f"Invalid button: {button}. Use 'left' or 'right'.")
    
    
    
    def execute_batch_moves(self, safe_moves: List[Tuple[int, int]], mine_cells: List[Tuple[int, int]], focus_tab: bool = True):
        """Execute both safe moves and flagging efficiently in one batch."""
        total_moves = len(safe_moves) + len(mine_cells)
        if total_moves == 0:
            return
            
        
        # Focus tab only if requested (to avoid unnecessary mouse movement)
        if focus_tab:
            self.select_tab()
        
        # Pre-calculate all coordinates to avoid redundant calculations
        mine_coords = []
        safe_coords = []
        
        for row, col in mine_cells:
            try:
                x, y = self.detector.get_cell_coordinates(row, col)
                mine_coords.append((x, y))
            except Exception:
                pass
        
        for row, col in safe_moves:
            try:
                x, y = self.detector.get_cell_coordinates(row, col)
                safe_coords.append((x, y))
            except Exception:
                pass
        
        # Execute flagging first (mines) - direct coordinate clicks
        for x, y in mine_coords:
            try:
                pyautogui.moveTo(x, y, duration=0.05)
                pyautogui.rightClick(x, y)
                time.sleep(0.03)
            except Exception:
                pass
        
        # Then execute safe moves - direct coordinate clicks
        for x, y in safe_coords:
            try:
                pyautogui.moveTo(x, y, duration=0.05)
                pyautogui.click(x, y)
                time.sleep(0.03)
            except Exception:
                pass
    
    def start_new_game(self):
        """Start a new game by clicking the smiley face."""
        # The smiley face is typically at the top center of the board
        if not self.detector:
            raise RuntimeError("Detector not set. Call set_detector() first.")
        
        # Focus the Minesweeper tab first
        self.select_tab()
        
        # Calculate smiley face position (approximate)
        board_config = self.detector.board_config
        smiley_x = board_config['x'] + (board_config['width'] // 2)
        smiley_y = board_config['y'] - 50  # Above the board
        
        pyautogui.click(smiley_x, smiley_y)
        time.sleep(0.5)  # Reduced wait for new game to start
    
