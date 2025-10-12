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
        
        # Configure pyautogui
        pyautogui.FAILSAFE = True  # Move mouse to corner to stop
        pyautogui.PAUSE = 0.1  # Small pause between actions
        
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
        
        self.logger.info(f"Selecting Minesweeper tab by clicking board center at ({center_x}, {center_y})")
        pyautogui.click(center_x, center_y)
        time.sleep(0.3)  # Brief wait for focus
    
    def set_difficulty(self, difficulty: str):
        """Set the game difficulty by clicking the dropdown."""
        if difficulty not in ['easy', 'medium', 'hard']:
            raise ValueError(f"Invalid difficulty: {difficulty}")
        
        self.logger.info(f"Setting difficulty to {difficulty}")
        
        # Medium is the default, no clicking needed
        if difficulty == 'medium':
            self.logger.info("Medium is default, no dropdown interaction needed")
            return
        
        # Focus the Minesweeper tab first
        self.select_tab()
        
        # Get dropdown coordinates
        dropdown_x = self.config.getint('difficulty_selector', 'dropdown_x')
        dropdown_y = self.config.getint('difficulty_selector', 'dropdown_y')
        
        # Click dropdown to open it
        pyautogui.click(dropdown_x, dropdown_y)
        time.sleep(0.5)  # Wait for dropdown to open
        
        # Click appropriate difficulty option
        if difficulty == 'easy':
            easy_x = self.config.getint('difficulty_selector', 'easy_x')
            easy_y = self.config.getint('difficulty_selector', 'easy_y')
            pyautogui.click(easy_x, easy_y)
            self.logger.info("Selected Easy difficulty")
        elif difficulty == 'hard':
            hard_x = self.config.getint('difficulty_selector', 'hard_x')
            hard_y = self.config.getint('difficulty_selector', 'hard_y')
            pyautogui.click(hard_x, hard_y)
            self.logger.info("Selected Hard difficulty")
        
        time.sleep(1.0)  # Wait for game to load
    
    def click_cell(self, row: int, col: int, button: str = 'left'):
        """Click a specific cell on the board."""
        if not self.detector:
            raise RuntimeError("Detector not set. Call set_detector() first.")
        
        # Focus the Minesweeper tab first
        self.select_tab()
        
        # Get cell coordinates from detector
        x, y = self.detector.get_cell_coordinates(row, col)
        
        # Debug logging
        self.logger.info(f"Clicking cell ({row}, {col}) at coordinates ({x}, {y})")
        
        # Get current screen size for validation
        screen_width, screen_height = pyautogui.size()
        self.logger.info(f"Screen size: {screen_width}x{screen_height}")
        
        # Validate coordinates are within screen bounds
        if x < 0 or x >= screen_width or y < 0 or y >= screen_height:
            self.logger.error(f"Coordinates ({x}, {y}) are outside screen bounds!")
            return
        
        # Move mouse to coordinates and click
        pyautogui.moveTo(x, y, duration=0.5)
        time.sleep(0.2)
        
        # Click the cell
        if button == 'left':
            pyautogui.click(x, y)
            self.logger.info(f"Left clicked cell ({row}, {col}) at ({x}, {y})")
        elif button == 'right':
            pyautogui.rightClick(x, y)
            self.logger.info(f"Right clicked cell ({row}, {col}) at ({x}, {y})")
        else:
            raise ValueError(f"Invalid button: {button}. Use 'left' or 'right'.")
        
        time.sleep(0.1)  # Small delay between clicks
    
    def click_safe_cells(self, safe_cells: List[Tuple[int, int]]):
        """Click multiple safe cells."""
        self.logger.info(f"Clicking {len(safe_cells)} safe cells")
        
        for row, col in safe_cells:
            try:
                self.click_cell(row, col, 'left')
                time.sleep(0.1)  # Small delay between clicks
            except Exception as e:
                self.logger.error(f"Failed to click cell ({row}, {col}): {e}")
    
    def flag_mines(self, mine_cells: List[Tuple[int, int]]):
        """Right-click to flag mine cells."""
        self.logger.info(f"Flagging {len(mine_cells)} mine cells")
        
        for row, col in mine_cells:
            try:
                self.click_cell(row, col, 'right')
                time.sleep(0.1)  # Small delay between clicks
            except Exception as e:
                self.logger.error(f"Failed to flag cell ({row}, {col}): {e}")
    
    def make_move(self, row: int, col: int, action: str = 'reveal'):
        """Make a move (reveal or flag) on a specific cell using double-click logic."""
        if action == 'reveal':
            self.click_cell(row, col, 'left')
        elif action == 'flag':
            self.click_cell(row, col, 'right')
        else:
            raise ValueError(f"Invalid action: {action}. Use 'reveal' or 'flag'.")
    
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
        time.sleep(1.0)  # Wait for new game to start
    
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
