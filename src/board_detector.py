import configparser
from typing import Dict, Tuple, Optional
import numpy as np
from PIL import Image
import mss
import cv2

class GoogleMinesweeperDetector:
    """Board detector for Google Minesweeper."""
    
    def __init__(self, config_path: str = "config.ini"):
        """Initialize the detector with configuration."""
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.current_difficulty = None
        self.board_config = None
        self.sct = mss.mss()
        
    def set_difficulty(self, difficulty: str):
        """Set the difficulty and load corresponding configuration."""
        if difficulty not in ['easy', 'medium', 'hard']:
            raise ValueError(f"Invalid difficulty: {difficulty}")
        
        self.current_difficulty = difficulty
        section_name = f"difficulty.{difficulty}"
        
        if not self.config.has_section(section_name):
            raise ValueError(f"Configuration section {section_name} not found")
        
        # Load board configuration
        self.board_config = {
            'width': self.config.getint(section_name, 'board_width'),
            'height': self.config.getint(section_name, 'board_height'),
            'x': self.config.getint(section_name, 'board_x'),
            'y': self.config.getint(section_name, 'board_y'),
            'rows': self.config.getint(section_name, 'grid_rows'),
            'cols': self.config.getint(section_name, 'grid_cols'),
            'cell_width': self.config.getfloat(section_name, 'cell_width'),
            'cell_height': self.config.getfloat(section_name, 'cell_height')
        }
        
    
    def capture_board(self) -> Image.Image:
        """Capture the game board screenshot."""
        if not self.board_config:
            raise RuntimeError("Difficulty not set. Call set_difficulty() first.")
        
        # Define screenshot area
        monitor = {
            "top": self.board_config['y'],
            "left": self.board_config['x'],
            "width": self.board_config['width'],
            "height": self.board_config['height']
        }
        
        # Capture screenshot
        screenshot = self.sct.grab(monitor)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        return img
    
    def analyze_board(self, image: Image.Image) -> Dict[Tuple[int, int], str]:
        """Analyze the board image and return cell states."""
        if not self.board_config:
            raise RuntimeError("Difficulty not set. Call set_difficulty() first.")
        
        board_state = {}
        
        # Convert PIL image to numpy array for processing
        img_array = np.array(image)
        
        for row in range(self.board_config['rows']):
            for col in range(self.board_config['cols']):
                # Calculate cell position in image
                cell_x = int(col * self.board_config['cell_width'])
                cell_y = int(row * self.board_config['cell_height'])
                cell_width = int(self.board_config['cell_width'])
                cell_height = int(self.board_config['cell_height'])
                
                # Extract cell region
                cell_region = img_array[
                    cell_y:cell_y + cell_height,
                    cell_x:cell_x + cell_width
                ]
                
                # Analyze cell content
                cell_state = self._analyze_cell(cell_region)
                board_state[(row, col)] = cell_state
        
        return board_state
    
    def _analyze_cell(self, cell_region: np.ndarray) -> str:
        """Analyze a single cell region to determine its state using color-based detection."""
        if len(cell_region.shape) != 3:
            # Convert grayscale to RGB if needed
            cell_region = cv2.cvtColor(cell_region, cv2.COLOR_GRAY2RGB)
        
        # Sample middle 80% of cell
        h, w = cell_region.shape[:2]
        center_h = int(h * 0.1) 
        center_w = int(w * 0.1) 
        center_region = cell_region[center_h:h-center_h, center_w:w-center_w]
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(center_region, cv2.COLOR_RGB2HSV)
        
        # Detect numbers 1-8 by their distinct colors
        number = self._detect_number_by_color(hsv)
        if number is not None:
            return str(number)
        
        # Check if cell is unopened
        if self._is_unopened_cell(hsv):
            return 'unopened'
        
        # Check if cell is revealed blank
        if self._is_blank_cell(hsv):
            return 'blank'
        
        # Default to unopened if uncertain
        return 'unopened'
    
    def _detect_number_by_color(self, hsv_region: np.ndarray) -> Optional[int]:
        """Detect number 1-8 by their distinct colors in HSV."""        
        
        # Color threshold ranges for numbers 1-8
        number_colors = {
            1: ([105, 140, 150], [115, 255, 255]),
            2: ([36, 108, 120], [76, 148, 160]),   
            3: ([0, 161, 174], [22, 201, 214]),    
            4: ([119, 171, 136], [159, 211, 176]), 
            5: ([0, 178, 220], [35, 218, 255]),    
            6: ([90, 150, 100], [110, 255, 220]),  
            7: ([0, 0, 20], [180, 50, 100]),       
            8: ([0, 0, 80], [180, 80, 200])        
        }
        
        best_match = None
        best_count = 0
        threshold = hsv_region.shape[0] * hsv_region.shape[1] * 0.1 
        
        for number, (lower, upper) in number_colors.items():
            # Create mask for color range
            lower = np.array(lower)
            upper = np.array(upper)
            mask = cv2.inRange(hsv_region, lower, upper)
            
            # Count matching pixels in mask
            count = cv2.countNonZero(mask)
            
            if count > best_count and count > threshold:
                best_count = count
                best_match = number
        
        return best_match
    
    def _is_blank_cell(self, hsv_region: np.ndarray) -> bool:
        """Check if cell is revealed blank (beige/tan color)."""
        lower_beige = np.array([15, 20, 140])
        upper_beige = np.array([35, 80, 255])
        
        mask = cv2.inRange(hsv_region, lower_beige, upper_beige)
        count = cv2.countNonZero(mask)
        
        threshold = hsv_region.shape[0] * hsv_region.shape[1] * 0.25 # higher threshold for blank cells
        return count > threshold
    
    def _is_unopened_cell(self, hsv_region: np.ndarray) -> bool:
        """Check if cell is unopened (bright green color)."""
        lower_green = np.array([80, 150, 180]) 
        upper_green = np.array([90, 255, 255]) 
        
        mask = cv2.inRange(hsv_region, lower_green, upper_green)
        count = cv2.countNonZero(mask)
        
        threshold = hsv_region.shape[0] * hsv_region.shape[1] * 0.4 # higher threshold for unopened cells
        return count > threshold
    
    def get_board_dimensions(self) -> Tuple[int, int]:
        """Get the current board dimensions (rows, cols)."""
        if not self.board_config:
            raise RuntimeError("Difficulty not set. Call set_difficulty() first.")
        
        return self.board_config['rows'], self.board_config['cols']
    
    def get_cell_coordinates(self, row: int, col: int) -> Tuple[int, int]:
        """Get the screen coordinates for a specific cell."""
        if not self.board_config:
            raise RuntimeError("Difficulty not set. Call set_difficulty() first.")
        
        # Calculate cell center coordinates
        cell_x = int(self.board_config['x'] + (col * self.board_config['cell_width']) + (self.board_config['cell_width'] / 2))
        cell_y = int(self.board_config['y'] + (row * self.board_config['cell_height']) + (self.board_config['cell_height'] / 2))
        
        return cell_x, cell_y
    
    def is_board_fresh(self, board_state: Dict[Tuple[int, int], str]) -> bool:
        """Check if board is completely unopened (fresh game)."""
        unopened_count = sum(1 for state in board_state.values() if state == 'unopened')
        total_cells = len(board_state)
        is_fresh = unopened_count == total_cells
        return is_fresh
    
