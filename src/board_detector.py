import logging
import configparser
from typing import Dict, Tuple, Optional
import numpy as np
from PIL import Image
import mss
import cv2
import time

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
        
        # Save PNG with unique timestamp for debugging
        timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
        debug_filename = f"ocr_board_{timestamp}.png"
        self.save_debug_image(image, debug_filename)
        
        # Debug: Print the board state as a grid
        self.logger.info("=== OCR DETECTED BOARD STATE ===")
        for row in range(self.board_config['rows']):
            row_str = ""
            for col in range(self.board_config['cols']):
                state = board_state.get((row, col), '?')
                if state == 'unopened':
                    row_str += "U "
                elif state == 'blank':
                    row_str += "B "
                elif state == 'flag':
                    row_str += "F "
                elif state.isdigit():
                    row_str += f"{state} "
                else:
                    row_str += "? "
            self.logger.info(f"Row {row:2d}: {row_str}")
        self.logger.info("=== END BOARD STATE ===")
        
        return board_state
    
    def _analyze_cell(self, cell_region: np.ndarray) -> str:
        """Analyze a single cell region to determine its state using color-based detection."""
        if len(cell_region.shape) != 3:
            # Convert grayscale to RGB if needed
            cell_region = cv2.cvtColor(cell_region, cv2.COLOR_GRAY2RGB)
        
        # Sample more of the cell (middle 80%) to better capture numbers
        h, w = cell_region.shape[:2]
        center_h = int(h * 0.1)  # Reduced from 0.2 to 0.1 (10% margin instead of 20%)
        center_w = int(w * 0.1)  # Reduced from 0.2 to 0.1 (10% margin instead of 20%)
        center_region = cell_region[center_h:h-center_h, center_w:w-center_w]
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(center_region, cv2.COLOR_RGB2HSV)
        
        # NOTE: Flag detection removed - flags are now tracked internally
        
        # Detect numbers 1-8 by their distinct colors (PRIORITY: check before blank cells)
        number = self._detect_number_by_color(hsv)
        if number is not None:
            return str(number)
        
        # Check if cell is unopened (bright green) - check before blank
        if self._is_unopened_cell(hsv):
            return 'unopened'
        
        # Check if cell is revealed blank (beige/tan color) - check LAST
        if self._is_blank_cell(hsv):
            return 'blank'
        
        # Default to unopened if uncertain
        return 'unopened'
    
    # Flag detection methods removed - flags are now tracked internally
    
    def _detect_number_by_color(self, hsv_region: np.ndarray) -> Optional[int]:
        """Detect number 1-8 by their distinct colors in HSV."""
        # Define color ranges based on actual RGB values from Google Minesweeper
        # Convert RGB to HSV and add tolerance ranges
        
        number_colors = {
            1: ([105, 140, 150], [115, 255, 255]),  # Blue: RGB(56, 116, 203) -> HSV(212, 72, 80)
            2: ([36, 108, 120], [76, 148, 160]),    # Green: RGB(80, 140, 70) -> HSV(56, 128, 140)
            3: ([0, 161, 174], [22, 201, 214]),     # Red: RGB(194, 63, 56) -> HSV(2, 181, 194)
            4: ([119, 171, 136], [159, 211, 176]),  # Purple: RGB(113, 39, 156) -> HSV(139, 191, 156)
            5: ([0, 178, 220], [35, 218, 255]),     # Orange: RGB(240, 149, 54) -> HSV(15, 198, 240)
            6: ([90, 150, 100], [110, 255, 220]),   # Cyan: RGB(0, 151, 167) -> HSV(184, 100, 65)
            7: ([0, 0, 20], [180, 50, 100]),        # Dark gray: RGB(66, 66, 66) -> HSV(0, 0, 26)
            8: ([0, 0, 80], [180, 80, 200])         # Light gray: RGB(156, 158, 159) -> HSV(0, 2, 62)
        }
        
        best_match = None
        best_count = 0
        threshold = hsv_region.shape[0] * hsv_region.shape[1] * 0.1  # 10% of pixels - more reasonable threshold
        
        for number, (lower, upper) in number_colors.items():
            # Create mask for this color range
            lower = np.array(lower)
            upper = np.array(upper)
            mask = cv2.inRange(hsv_region, lower, upper)
            
            # Count matching pixels
            count = cv2.countNonZero(mask)
            
            # Debug logging for numbers 2, 3, 4, and 5
            if number in [2, 3, 4, 5]:  # Log all detection attempts for problematic numbers
                self.logger.debug(f"Number {number}: {count} pixels (threshold: {threshold}) - {'MATCH' if count > threshold else 'below threshold'}")
            
            if count > best_count and count > threshold:
                best_count = count
                best_match = number
        
        return best_match
    
    def _is_blank_cell(self, hsv_region: np.ndarray) -> bool:
        """Check if cell is revealed blank (beige/tan color)."""
        # Blank cells: RGB(215, 184, 153) or RGB(229, 194, 159) -> HSV(25, 29, 84) or HSV(26, 31, 90)
        # Beige/tan colors: low saturation, medium-high brightness
        lower_beige = np.array([15, 20, 140])  # Light beige - wider range
        upper_beige = np.array([35, 80, 255])  # Light tan - wider range
        
        mask = cv2.inRange(hsv_region, lower_beige, upper_beige)
        count = cv2.countNonZero(mask)
        
        # Lower threshold since blank cells might be smaller portions
        threshold = hsv_region.shape[0] * hsv_region.shape[1] * 0.25
        return count > threshold
    
    def _is_unopened_cell(self, hsv_region: np.ndarray) -> bool:
        """Check if cell is unopened (bright green color)."""
        # Unopened cells: RGB(170, 215, 80) or RGB(162, 209, 72) -> HSV(84, 63, 84) or HSV(86, 66, 82)
        # Need to distinguish from number 2 which is darker green
        lower_green = np.array([80, 150, 180])  # Bright green unopened cells
        upper_green = np.array([90, 255, 255])  # Very bright green
        
        mask = cv2.inRange(hsv_region, lower_green, upper_green)
        count = cv2.countNonZero(mask)
        
        # Need significant bright green pixels to be considered unopened
        # Higher threshold to avoid confusion with number 2
        threshold = hsv_region.shape[0] * hsv_region.shape[1] * 0.4
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
        cell_x = self.board_config['x'] + (col * self.board_config['cell_width']) + (self.board_config['cell_width'] // 2)
        cell_y = self.board_config['y'] + (row * self.board_config['cell_height']) + (self.board_config['cell_height'] // 2)
        
        # Debug logging
        self.logger.info(f"Cell ({row}, {col}) coordinates: board at ({self.board_config['x']}, {self.board_config['y']}), "
                        f"cell size {self.board_config['cell_width']}x{self.board_config['cell_height']}, "
                        f"final coords ({cell_x}, {cell_y})")
        
        return cell_x, cell_y
    
    def is_board_fresh(self, board_state: Dict[Tuple[int, int], str]) -> bool:
        """Check if board is completely unopened (fresh game)."""
        unopened_count = sum(1 for state in board_state.values() if state == 'unopened')
        total_cells = len(board_state)
        is_fresh = unopened_count == total_cells
        self.logger.info(f"Board freshness check: {unopened_count}/{total_cells} unopened cells - {'FRESH' if is_fresh else 'IN_PROGRESS'}")
        return is_fresh
    
    def save_debug_image(self, image: Image.Image, filename: str = "debug_board.png"):
        """Save board image for debugging purposes."""
        image.save(f"temp/{filename}")
        self.logger.info(f"Saved debug image: temp/{filename}")
