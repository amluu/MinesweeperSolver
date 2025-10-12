import logging
import configparser
from typing import Dict, Tuple, Optional
import numpy as np
from PIL import Image
import mss
import cv2

class GoogleMinesweeperDetector:
    """Board detector for Google Minesweeper using hardcoded coordinates."""
    
    def __init__(self, config_path: str = "config.ini"):
        """Initialize the detector with configuration."""
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.logger = logging.getLogger(__name__)
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
            'cell_width': self.config.getint(section_name, 'cell_width'),
            'cell_height': self.config.getint(section_name, 'cell_height')
        }
        
        self.logger.info(f"Set difficulty to {difficulty}: {self.board_config['rows']}x{self.board_config['cols']} grid")
    
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
        
        self.logger.debug(f"Captured board: {img.size}")
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
                cell_x = col * self.board_config['cell_width']
                cell_y = row * self.board_config['cell_height']
                
                # Extract cell region
                cell_region = img_array[
                    cell_y:cell_y + self.board_config['cell_height'],
                    cell_x:cell_x + self.board_config['cell_width']
                ]
                
                # Analyze cell content
                cell_state = self._analyze_cell(cell_region)
                board_state[(row, col)] = cell_state
        
        return board_state
    
    def _analyze_cell(self, cell_region: np.ndarray) -> str:
        """Analyze a single cell region to determine its state."""
        # Convert to grayscale for analysis
        if len(cell_region.shape) == 3:
            gray = cv2.cvtColor(cell_region, cv2.COLOR_RGB2GRAY)
        else:
            gray = cell_region
        
        # Get average color of the cell
        avg_color = np.mean(gray)
        
        # Check for flag (red color)
        if self._has_flag(cell_region):
            return 'flag'
        
        # Check for revealed number
        number = self._detect_number(cell_region)
        if number is not None:
            return str(number)
        
        # Check if cell is blank (revealed but no number)
        if avg_color > 200:  # Light color indicates revealed blank cell
            return 'blank'
        
        # Default to unopened
        return 'unopened'
    
    def _has_flag(self, cell_region: np.ndarray) -> bool:
        """Check if cell contains a flag."""
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(cell_region, cv2.COLOR_RGB2HSV)
        
        # Define red color range for flag
        lower_red = np.array([0, 50, 50])
        upper_red = np.array([10, 255, 255])
        
        # Create mask for red pixels
        mask = cv2.inRange(hsv, lower_red, upper_red)
        
        # Count red pixels
        red_pixels = cv2.countNonZero(mask)
        
        # Flag if significant red pixels present
        return red_pixels > (cell_region.shape[0] * cell_region.shape[1] * 0.1)
    
    def _detect_number(self, cell_region: np.ndarray) -> Optional[int]:
        """Detect number in a revealed cell."""
        # Convert to grayscale
        if len(cell_region.shape) == 3:
            gray = cv2.cvtColor(cell_region, cv2.COLOR_RGB2GRAY)
        else:
            gray = cell_region
        
        # Simple number detection based on average brightness
        # This is a simplified approach - could be enhanced with OCR
        avg_brightness = np.mean(gray)
        
        # Check for specific number colors
        # This is a basic implementation - would need refinement based on actual game colors
        if avg_brightness < 100:  # Dark numbers
            # Count dark pixels to estimate number
            dark_pixels = np.sum(gray < 100)
            total_pixels = gray.shape[0] * gray.shape[1]
            
            if dark_pixels > total_pixels * 0.3:  # Significant dark content
                # This is a placeholder - real implementation would use OCR or template matching
                # For now, return a placeholder number
                return 1  # Placeholder
        
        return None
    
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
        cell_x = self.board_config['x'] + (col * self.board_config['cell_width']) + (self.board_config['cell_width'] // 2)
        cell_y = self.board_config['y'] + (row * self.board_config['cell_height']) + (self.board_config['cell_height'] // 2)
        
        # Debug logging
        self.logger.info(f"Cell ({row}, {col}) coordinates: board at ({self.board_config['x']}, {self.board_config['y']}), "
                        f"cell size {self.board_config['cell_width']}x{self.board_config['cell_height']}, "
                        f"final coords ({cell_x}, {cell_y})")
        
        return cell_x, cell_y
    
    def save_debug_image(self, image: Image.Image, filename: str = "debug_board.png"):
        """Save board image for debugging purposes."""
        image.save(f"temp/{filename}")
        self.logger.info(f"Saved debug image: temp/{filename}")
