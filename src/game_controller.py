import logging
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
        self.logger = logging.getLogger(__name__)
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
        
        self.logger.debug(f"Selecting Minesweeper tab by clicking board center at ({center_x}, {center_y})")
        pyautogui.click(center_x, center_y)
        time.sleep(0.1)  # Reduced wait for focus
    
    def set_difficulty(self, difficulty: str):
        """Set the game difficulty - user must manually select difficulty."""
        if difficulty not in ['easy', 'medium', 'hard']:
            raise ValueError(f"Invalid difficulty: {difficulty}")
        
        self.logger.info(f"Difficulty set to {difficulty} - user must manually select this in the game")
        
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
        
        # Debug logging
        self.logger.debug(f"Clicking cell ({row}, {col}) at coordinates ({x}, {y})")
        
        # Get current screen size for validation
        screen_width, screen_height = pyautogui.size()
        
        # Validate coordinates are within screen bounds
        if x < 0 or x >= screen_width or y < 0 or y >= screen_height:
            self.logger.error(f"Coordinates ({x}, {y}) are outside screen bounds!")
            return
        
        # Move mouse to coordinates quickly and click
        pyautogui.moveTo(x, y, duration=0.1)  # Much faster movement
        
        # Click the cell
        if button == 'left':
            pyautogui.click(x, y)
            self.logger.debug(f"Left clicked cell ({row}, {col}) at ({x}, {y})")
        elif button == 'right':
            pyautogui.rightClick(x, y)
            self.logger.debug(f"Right clicked cell ({row}, {col}) at ({x}, {y})")
        else:
            raise ValueError(f"Invalid button: {button}. Use 'left' or 'right'.")
    
    def click_safe_cells(self, safe_cells: List[Tuple[int, int]]):
        """Click multiple safe cells efficiently."""
        if not safe_cells:
            return
            
        self.logger.info(f"Clicking {len(safe_cells)} safe cells")
        
        # Focus tab only once at the beginning
        self.select_tab()
        
        # Pre-calculate all coordinates
        coords = []
        for row, col in safe_cells:
            try:
                x, y = self.detector.get_cell_coordinates(row, col)
                coords.append((x, y))
            except Exception as e:
                self.logger.error(f"Failed to get coordinates for cell ({row}, {col}): {e}")
        
        # Execute clicks with pre-calculated coordinates
        for x, y in coords:
            try:
                pyautogui.moveTo(x, y, duration=0.05)
                pyautogui.click(x, y)
                time.sleep(0.03)
            except Exception as e:
                self.logger.error(f"Failed to click at coordinates ({x}, {y}): {e}")
    
    def flag_mines(self, mine_cells: List[Tuple[int, int]]):
        """Right-click to flag mine cells efficiently."""
        if not mine_cells:
            return
            
        self.logger.info(f"Flagging {len(mine_cells)} mine cells")
        
        # Focus tab only once at the beginning
        self.select_tab()
        
        # Pre-calculate all coordinates
        coords = []
        for row, col in mine_cells:
            try:
                x, y = self.detector.get_cell_coordinates(row, col)
                coords.append((x, y))
            except Exception as e:
                self.logger.error(f"Failed to get coordinates for mine cell ({row}, {col}): {e}")
        
        # Execute right-clicks with pre-calculated coordinates
        for x, y in coords:
            try:
                pyautogui.moveTo(x, y, duration=0.05)
                pyautogui.rightClick(x, y)
                time.sleep(0.03)
            except Exception as e:
                self.logger.error(f"Failed to flag at coordinates ({x}, {y}): {e}")
    
    def make_move(self, row: int, col: int, action: str = 'reveal'):
        """Make a move (reveal or flag) on a specific cell using double-click logic."""
        if action == 'reveal':
            self.click_cell(row, col, 'left')
        elif action == 'flag':
            self.click_cell(row, col, 'right')
        else:
            raise ValueError(f"Invalid action: {action}. Use 'reveal' or 'flag'.")
    
    def execute_batch_moves(self, safe_moves: List[Tuple[int, int]], mine_cells: List[Tuple[int, int]], focus_tab: bool = True):
        """Execute both safe moves and flagging efficiently in one batch."""
        total_moves = len(safe_moves) + len(mine_cells)
        if total_moves == 0:
            return
            
        self.logger.info(f"Executing batch: {len(safe_moves)} safe moves, {len(mine_cells)} flags")
        
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
            except Exception as e:
                self.logger.error(f"Failed to get coordinates for mine cell ({row}, {col}): {e}")
        
        for row, col in safe_moves:
            try:
                x, y = self.detector.get_cell_coordinates(row, col)
                safe_coords.append((x, y))
            except Exception as e:
                self.logger.error(f"Failed to get coordinates for safe cell ({row}, {col}): {e}")
        
        # Execute flagging first (mines) - direct coordinate clicks
        for x, y in mine_coords:
            try:
                pyautogui.moveTo(x, y, duration=0.05)
                pyautogui.rightClick(x, y)
                time.sleep(0.03)
            except Exception as e:
                self.logger.error(f"Failed to flag at coordinates ({x}, {y}): {e}")
        
        # Then execute safe moves - direct coordinate clicks
        for x, y in safe_coords:
            try:
                pyautogui.moveTo(x, y, duration=0.05)
                pyautogui.click(x, y)
                time.sleep(0.03)
            except Exception as e:
                self.logger.error(f"Failed to click at coordinates ({x}, {y}): {e}")
    
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
        
        self.logger.info(f"Clicking smiley face at ({smiley_x}, {smiley_y}) to start new game")
        pyautogui.click(smiley_x, smiley_y)
        self.logger.info("Clicked smiley face to start new game")
        time.sleep(0.5)  # Reduced wait for new game to start
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position for debugging."""
        return pyautogui.position()
    
    def move_mouse_to_cell(self, row: int, col: int):
        """Move mouse to a specific cell without clicking."""
        if not self.detector:
            raise RuntimeError("Detector not set. Call set_detector() first.")
        
        x, y = self.detector.get_cell_coordinates(row, col)
        pyautogui.moveTo(x, y)
        self.logger.debug(f"Moved mouse to cell ({row}, {col}) at ({x}, {y})")
    
    def test_coordinates(self):
        """Test coordinate system by moving to known positions."""
        if not self.detector:
            raise RuntimeError("Detector not set. Call set_detector() first.")
        
        self.logger.info("Testing coordinate system...")
        
        # Test board corner coordinates
        board_config = self.detector.board_config
        top_left = (board_config['x'], board_config['y'])
        top_right = (board_config['x'] + board_config['width'], board_config['y'])
        bottom_left = (board_config['x'], board_config['y'] + board_config['height'])
        bottom_right = (board_config['x'] + board_config['width'], board_config['y'] + board_config['height'])
        
        test_positions = [
            ("Top-left corner", top_left),
            ("Top-right corner", top_right),
            ("Bottom-left corner", bottom_left),
            ("Bottom-right corner", bottom_right)
        ]
        
        for name, (x, y) in test_positions:
            self.logger.info(f"Moving to {name}: ({x}, {y})")
            pyautogui.moveTo(x, y, duration=1.0)
            time.sleep(2)
        
        # Test first few cells
        for row in range(min(3, board_config['rows'])):
            for col in range(min(3, board_config['cols'])):
                x, y = self.detector.get_cell_coordinates(row, col)
                self.logger.info(f"Moving to cell ({row}, {col}): ({x}, {y})")
                pyautogui.moveTo(x, y, duration=0.5)
                time.sleep(1)
