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
import configparser

class GameController:
    """Controls the browser automation and game execution."""
    
    def __init__(self, difficulty: str, status_callback=None):
        """Initialize the game controller with a specific difficulty."""
        self.difficulty = difficulty
        self.config = load_difficulty_config(difficulty)
        self.tesseract_path = get_tesseract_path()
        self.status_callback = status_callback  # Callback for GUI status updates
        
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
            
            # Wait for human to complete captcha if present
            self._wait_for_captcha_completion()
            
            # Click play button - try multiple selectors for robustness
            play_button = None
            play_button_selectors = [
                (By.CSS_SELECTOR, 'div[role="button"][jsname="JNZWEd"]'),  # Primary selector from dev tools
                (By.CSS_SELECTOR, 'div[jsname="JNZWEd"]'),  # Fallback without role
                (By.CLASS_NAME, "fxvhbc"),  # Original selector as fallback
                (By.CSS_SELECTOR, 'div[role="button"].TX'),  # Alternative selector
            ]
            
            for selector_type, selector_value in play_button_selectors:
                try:
                    play_button = self.driver.find_element(selector_type, selector_value)
                    if play_button.is_displayed() and play_button.is_enabled():
                        break
                except NoSuchElementException:
                    continue
            
            if play_button is None:
                # Take a screenshot for debugging
                try:
                    self.driver.save_screenshot("temp/play_button_debug.png")
                    self.logger.error("Could not find play button - screenshot saved to temp/play_button_debug.png")
                except:
                    pass
                raise NoSuchElementException("Could not find play button with any selector")
            
            self.logger.info(f"Found play button using selector: {play_button_selectors[0] if play_button else 'unknown'}")
            play_button.click()
            time.sleep(1)  # Wait for page to load after clicking
            
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
    
    def _wait_for_captcha_completion(self):
        """Wait for user to complete any captcha that appears."""
        try:
            # Check for common captcha indicators
            captcha_selectors = [
                "iframe[src*='recaptcha']",
                ".g-recaptcha",
                "#captcha",
                ".captcha",
                "[data-callback*='recaptcha']",
                "div[data-sitekey]"
            ]
            
            captcha_found = False
            for selector in captcha_selectors:
                try:
                    captcha_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if captcha_element.is_displayed():
                        captcha_found = True
                        break
                except NoSuchElementException:
                    continue
            
            if captcha_found:
                self.logger.info("CAPTCHA detected! Please complete the captcha in the browser window.")
                
                # Update GUI status if callback is available
                if self.status_callback:
                    self.status_callback("CAPTCHA detected - Please complete in browser")
                
                print("\n" + "="*60)
                print("🤖 CAPTCHA DETECTED")
                print("="*60)
                print("A captcha has appeared in the browser window.")
                print("Please complete the captcha manually.")
                print("The solver will continue automatically once the captcha is solved.")
                print("="*60 + "\n")
                
                # Wait for captcha to be completed
                import time
                config = configparser.ConfigParser()
                config.read('config.ini')
                max_wait_time = config.getint('captcha', 'timeout_seconds', fallback=300)
                check_interval = config.getint('captcha', 'check_interval', fallback=2)
                waited_time = 0
                
                while waited_time < max_wait_time:
                    time.sleep(check_interval)
                    waited_time += check_interval
                    
                    # Check if captcha is still present
                    captcha_still_present = False
                    for selector in captcha_selectors:
                        try:
                            captcha_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if captcha_element.is_displayed():
                                captcha_still_present = True
                                break
                        except NoSuchElementException:
                            continue
                    
                    if not captcha_still_present:
                        self.logger.info("Captcha completed! Continuing with solver...")
                        print("✅ Captcha completed! Continuing with solver...")
                        
                        # Update GUI status
                        if self.status_callback:
                            self.status_callback("Captcha completed - Continuing...")
                        break
                    
                    # Show progress every 30 seconds
                    if waited_time % 30 == 0:
                        remaining = max_wait_time - waited_time
                        progress_msg = f"Waiting for captcha completion... ({remaining}s remaining)"
                        print(f"⏳ {progress_msg}")
                        
                        # Update GUI status
                        if self.status_callback:
                            self.status_callback(progress_msg)
                
                if waited_time >= max_wait_time:
                    self.logger.warning("Timeout waiting for captcha completion")
                    print("⚠️ Timeout waiting for captcha completion")
            else:
                self.logger.info("No captcha detected, proceeding normally")
                
        except Exception as e:
            self.logger.warning(f"Error checking for captcha: {e}")
            print(f"⚠️ Could not check for captcha: {e}")

    def _select_difficulty(self):
        """Select the appropriate difficulty level."""
        if self.difficulty == "easy":
            # Easy is already selected by default
            return
        
        try:
            # Try multiple selectors for difficulty selector button
            difficulty_selector = None
            selector_attempts = [
                (By.CLASS_NAME, "fHwb5b"),  # Original selector
                (By.CSS_SELECTOR, 'div[role="button"]:contains("Difficulty")'),
                (By.CSS_SELECTOR, 'button:contains("Difficulty")'),
                (By.XPATH, "//button[contains(text(), 'Difficulty')]"),
            ]
            
            for selector_type, selector_value in selector_attempts:
                try:
                    difficulty_selector = self.driver.find_element(selector_type, selector_value)
                    if difficulty_selector.is_displayed() and difficulty_selector.is_enabled():
                        break
                except (NoSuchElementException, Exception):
                    continue
            
            if difficulty_selector is None:
                self.logger.warning(f"Could not find difficulty selector for {self.difficulty}")
                return
            
            difficulty_selector.click()
            time.sleep(0.5)  # Wait for menu to appear
            
            # Find the appropriate menu item with multiple selector attempts
            menu_selectors = [
                "g-menu-item.EpPYLd.GZnQqe.WtV5nd",
                "div[role='menuitem']",
                ".menu-item",
                "[role='menuitem']"
            ]
            
            menu_items = []
            for selector in menu_selectors:
                try:
                    menu_items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if menu_items:
                        break
                except Exception:
                    continue
            
            if self.difficulty == "medium" and len(menu_items) > 1:
                # Medium is typically the second option
                menu_items[1].click()
            elif self.difficulty == "hard" and len(menu_items) > 2:
                # Hard is typically the third option
                hard_button = menu_items[2]
                self.actions.move_to_element_with_offset(hard_button, 0, 50)
                self.actions.click().perform()
            else:
                self.logger.warning(f"Could not find menu items for difficulty selection")
                
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
