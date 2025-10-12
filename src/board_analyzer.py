import cv2
import numpy as np
import pytesseract
import configparser
import logging
from typing import Dict, Tuple, Set, Optional
from dataclasses import dataclass

@dataclass
class DifficultyConfig:
    """Configuration for a specific difficulty level."""
    x: int
    y: int
    width: int
    height: int
    cell_size: int
    rows: int
    cols: int

class BoardAnalyzer:
    """Handles board analysis, OCR, and change detection."""
    
    def __init__(self, config: DifficultyConfig, tesseract_path: str):
        """Initialize the board analyzer with configuration."""
        self.config = config
        self.tesseract_path = tesseract_path
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Color definitions for cell detection
        self.blank_color_light = (164, 196, 224)
        self.blank_color_dark = (157, 185, 210)
        self.unopened_color_light = (102, 214, 179)
        self.unopened_color_dark = (95, 208, 172)
        self.color_threshold = 25
        
        # Cache for previous board state to detect changes
        self.previous_board: Optional[Dict[Tuple[int, int], str]] = None
        
        self.logger = logging.getLogger(__name__)
    
    def analyze_screenshot(self, image_path: str) -> Dict[Tuple[int, int], str]:
        """
        Analyze a screenshot and return the board state.
        Only analyzes cells that have changed since the last analysis.
        """
        image = cv2.imread(image_path)
        if image is None:
            self.logger.error(f"Could not load image: {image_path}")
            return {}
        
        # Crop the image to the board area
        cropped_image = image[
            self.config.y:self.config.y + self.config.height,
            self.config.x:self.config.x + self.config.width
        ]
        
        # Save cropped image for win detection
        cv2.imwrite("temp/croppedimage.png", cropped_image)
        
        # Determine which cells to analyze
        cells_to_analyze = self._get_cells_to_analyze()
        
        # Analyze only the changed cells
        board = {}
        if self.previous_board:
            board = self.previous_board.copy()
        
        for row, col in cells_to_analyze:
            cell_image = self._extract_cell(cropped_image, row, col)
            content = self._get_cell_content(cell_image)
            board[(row, col)] = content
        
        # Update cache
        self.previous_board = board.copy()
        
        return board
    
    def _get_cells_to_analyze(self) -> Set[Tuple[int, int]]:
        """Determine which cells need to be analyzed."""
        if self.previous_board is None:
            # First analysis - analyze all cells
            return {(row, col) for row in range(self.config.rows) 
                   for col in range(self.config.cols)}
        
        # For now, analyze all cells on subsequent runs
        # TODO: Implement smart change detection to only analyze changed cells
        return {(row, col) for row in range(self.config.rows) 
               for col in range(self.config.cols)}
    
    def _extract_cell(self, cropped_image: np.ndarray, row: int, col: int) -> np.ndarray:
        """Extract a single cell from the cropped board image."""
        y_start = row * self.config.cell_size
        x_start = col * self.config.cell_size
        y_end = y_start + self.config.cell_size
        x_end = x_start + self.config.cell_size
        
        return cropped_image[y_start:y_end, x_start:x_end]
    
    def _get_cell_content(self, cell: np.ndarray) -> str:
        """Analyze a cell image and determine its content."""
        # Convert to grayscale and apply threshold
        gray_cell = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
        _, thresh_cell = cv2.threshold(gray_cell, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        # Resize for better OCR
        resized_gray_cell = cv2.resize(thresh_cell, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # Try OCR first
        extracted_text = pytesseract.image_to_string(
            resized_gray_cell, 
            config='--psm 10 -c tessedit_char_whitelist=012345678'
        )
        
        if extracted_text.strip():
            return extracted_text.strip()
        
        # If OCR fails, use color detection
        average_color = cv2.mean(cell)[:3]
        
        # Check for blank cells
        if (self._color_matches(average_color, self.blank_color_light) or 
            self._color_matches(average_color, self.blank_color_dark)):
            return 'blank'
        
        # Check for unopened cells
        if (self._color_matches(average_color, self.unopened_color_light) or 
            self._color_matches(average_color, self.unopened_color_dark)):
            return 'unopened'
        
        return "unknown"
    
    def _color_matches(self, color1: Tuple[float, float, float], 
                      color2: Tuple[int, int, int]) -> bool:
        """Check if two colors match within the threshold."""
        return all(abs(color1[i] - color2[i]) < self.color_threshold for i in range(3))
    
    def check_win_condition(self) -> bool:
        """Check if the game has been won by looking for the win screen."""
        try:
            source_image = cv2.imread('temp/croppedimage.png')
            template_image = cv2.imread('assets/WinReq.png')
            
            if source_image is None or template_image is None:
                return False
            
            result = cv2.matchTemplate(source_image, template_image, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            return max_val >= 0.8
        except Exception as e:
            self.logger.error(f"Error checking win condition: {e}")
            return False
    
    def reset_cache(self):
        """Reset the board cache (call when starting a new game)."""
        self.previous_board = None

def load_difficulty_config(difficulty: str) -> DifficultyConfig:
    """Load configuration for a specific difficulty level."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    if difficulty not in config:
        raise ValueError(f"Unknown difficulty: {difficulty}")
    
    section = config[difficulty]
    return DifficultyConfig(
        x=int(section['x']),
        y=int(section['y']),
        width=int(section['width']),
        height=int(section['height']),
        cell_size=int(section['cell_size']),
        rows=int(section['rows']),
        cols=int(section['cols'])
    )

def get_tesseract_path() -> str:
    """Get the tesseract path from config."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['tesseract']['path']
