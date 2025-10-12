import time
import logging
from typing import List, Tuple, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException

from .board_analyzer import BoardAnalyzer, DifficultyConfig, load_difficulty_config, get_tesseract_path
from .solver import MinesweeperSolver

class GameController:
    """Controls the browser automation and game execution."""
    
    def __init__(self, difficulty: str):
        """Initialize the game controller with a specific difficulty."""
        self.difficulty = difficulty
        self.config = load_difficulty_config(difficulty)
        self.tesseract_path = get_tesseract_path()
        
        # Initialize components
        self.board_analyzer = BoardAnalyzer(self.config, self.tesseract_path)
        self.solver = MinesweeperSolver(self.config.rows, self.config.cols)
        
        # Browser components
        self.driver: Optional[webdriver.Chrome] = None
        self.actions: Optional[ActionChains] = None
        
        self.logger = logging.getLogger(__name__)
    
    def setup_browser(self) -> webdriver.Chrome:
        """Set up and return a configured Chrome driver."""
        options = Options()
        options.add_experimental_option("detach", True)
        
        self.driver = webdriver.Chrome(options=options)
        self.actions = ActionChains(self.driver)
        
        self.logger.info("Browser setup complete")
        return self.driver
    
    def start_game(self) -> bool:
        """Navigate to the game and start a new game. Returns True if successful."""
        try:
            # Navigate to Google Minesweeper
            self.driver.get("https://g.co/kgs/uCmazF6")
            self.driver.maximize_window()
            
            # Wait for page to load
            self.driver.implicitly_wait(2)
            
            # Click play button
            play_button = self.driver.find_element(By.CLASS_NAME, "fxvhbc")
            play_button.click()
            
            # Select difficulty if needed
            self._select_difficulty()
            
            # Click on board to start game
            board = self.driver.find_element(By.CLASS_NAME, "ecwpfc")
            board.click()
            
            self.logger.info(f"Started {self.difficulty} game successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start game: {e}")
            return False
    
    def _select_difficulty(self):
        """Select the appropriate difficulty level."""
        if self.difficulty == "easy":
            # Easy is already selected by default
            return
        
        try:
            difficulty_selector = self.driver.find_element(By.CLASS_NAME, "fHwb5b")
            difficulty_selector.click()
            
            # Find the appropriate menu item
            if self.difficulty == "medium":
                # Medium is the second option (index 1)
                medium_button = self.driver.find_elements(By.CSS_SELECTOR, "g-menu-item.EpPYLd.GZnQqe.WtV5nd")[1]
                medium_button.click()
            elif self.difficulty == "hard":
                # Hard is the third option (index 2)
                hard_button = self.driver.find_elements(By.CSS_SELECTOR, "g-menu-item.EpPYLd.GZnQqe.WtV5nd")[2]
                self.actions.move_to_element_with_offset(hard_button, 0, 50)
                self.actions.click().perform()
                
        except Exception as e:
            self.logger.warning(f"Could not select difficulty {self.difficulty}: {e}")
    
    def execute_moves(self, moves: List[Tuple[int, int]]) -> None:
        """Execute a list of moves on the board."""
        if not moves:
            return
        
        try:
            xbutton = self.driver.find_element(By.ID, 'eqeexb')
            location = xbutton.location
            
            for row, col in moves:
                self._click_cell(row, col, xbutton, location)
                time.sleep(0.1)  # Small delay between clicks
                
            self.logger.info(f"Executed {len(moves)} moves")
            
        except Exception as e:
            self.logger.error(f"Failed to execute moves: {e}")
    
    def _click_cell(self, row: int, col: int, xbutton, location: dict) -> None:
        """Click on a specific cell."""
        # Calculate coordinates based on difficulty
        if self.difficulty == "hard":
            # Hard mode uses different coordinate calculation
            yCoord = (row * self.config.cell_size) + self.config.cell_size/2 + self.config.y
            xCoord = (col * self.config.cell_size) + self.config.cell_size/2 + self.config.x
        else:
            # Easy and medium use the same calculation
            yCoord = (row + 1) * self.config.cell_size - (self.config.cell_size/2) + self.config.y
            xCoord = (col + 1) * self.config.cell_size - (self.config.cell_size/2) + self.config.x
        
        # Calculate offset from reference button
        offset_x = (xCoord/2) - location['x']
        offset_y = (yCoord/2) - location['y']
        
        # Perform the click
        self.actions.move_to_element_with_offset(xbutton, offset_x, offset_y).click().perform()
        self.logger.debug(f"Clicked cell ({row}, {col})")
    
    def take_screenshot(self, filename: str = "temp/webBrowser.png") -> str:
        """Take a screenshot and return the filename."""
        self.driver.save_screenshot(filename)
        return filename
    
    def run(self) -> bool:
        """
        Run the complete game automation.
        Returns True if the game was completed successfully.
        """
        try:
            # Setup browser
            self.setup_browser()
            
            # Start game
            if not self.start_game():
                return False
            
            # Wait for game to load
            time.sleep(2)
            
            # Game loop
            self.board_analyzer.reset_cache()
            game_running = True
            move_count = 0
            
            while game_running:
                # Take screenshot
                screenshot_path = self.take_screenshot()
                
                # Analyze board
                board = self.board_analyzer.analyze_screenshot(screenshot_path)
                
                # Find next moves
                next_moves = self.solver.find_safe_moves(board)
                
                if next_moves:
                    # Execute moves
                    self.execute_moves(next_moves)
                    move_count += len(next_moves)
                    
                    # Check win condition
                    if self.board_analyzer.check_win_condition():
                        self.logger.info("Game completed successfully!")
                        game_running = False
                        
                else:
                    # No safe moves available
                    self.logger.info("No safe moves detected. Game may require guessing.")
                    game_running = False
                
                # Safety check to prevent infinite loops
                if move_count > 1000:
                    self.logger.warning("Too many moves, stopping to prevent infinite loop")
                    break
            
            return True
            
        except Exception as e:
            self.logger.error(f"Game execution failed: {e}")
            return False
        
        finally:
            if self.driver:
                # Don't close browser automatically - let user see the result
                pass
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
