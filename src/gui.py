import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
import time
from typing import Optional, Callable
from .board_detector import GoogleMinesweeperDetector
from .game_controller import GoogleMinesweeperController
from .solver import MinesweeperSolver

class UniversalMinesweeperGUI:
    """GUI for universal minesweeper solver."""
    
    def __init__(self):
        """Initialize the GUI."""
        self.root = tk.Tk()
        self.solver_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.detector = GoogleMinesweeperDetector()
        self.controller = GoogleMinesweeperController()
        self.solver = None
        
        self.controller.set_detector(self.detector)
        
        self._setup_gui()
    
    def _setup_gui(self):
        """Set up the GUI components."""
        self.root.title("Google Minesweeper Solver")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Google Minesweeper Solver", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Difficulty selection frame
        difficulty_frame = ttk.LabelFrame(main_frame, text="Difficulty Selection", padding="10")
        difficulty_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(difficulty_frame, text="Difficulty:").grid(row=0, column=0, padx=(0, 10))
        
        self.difficulty_var = tk.StringVar(value="medium")
        self.difficulty_combo = ttk.Combobox(difficulty_frame, textvariable=self.difficulty_var,
                                           values=["easy", "medium", "hard"], state="readonly")
        self.difficulty_combo.grid(row=0, column=1, padx=(0, 10))
        
        self.set_difficulty_btn = ttk.Button(difficulty_frame, text="Set Difficulty", 
                                           command=self._set_difficulty)
        self.set_difficulty_btn.grid(row=0, column=2, padx=(0, 10))
        
        self.test_coords_btn = ttk.Button(difficulty_frame, text="Test Coordinates", 
                                        command=self._test_coordinates)
        self.test_coords_btn.grid(row=0, column=3, padx=(0, 10))
        
        self.get_mouse_btn = ttk.Button(difficulty_frame, text="Get Mouse Pos", 
                                      command=self._get_mouse_position)
        self.get_mouse_btn.grid(row=0, column=4)
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                                text="Select difficulty and start solver. Make sure Google Minesweeper is open at 110% zoom!",
                                justify=tk.LEFT)
        instructions.grid(row=2, column=0, columnspan=3, pady=(0, 20))
        
        # Control buttons frame
        control_frame = ttk.LabelFrame(main_frame, text="Solver Control", padding="10")
        control_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.start_btn = ttk.Button(control_frame, text="Start Solver", 
                                   command=self._start_solver)
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", 
                                  command=self._stop_solver, state="disabled")
        self.stop_btn.grid(row=0, column=1)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        self.status_var = tk.StringVar(value="Ready - Select difficulty and start solver")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, wraplength=450)
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(0, weight=1)
    
    def _set_difficulty(self):
        """Set the game difficulty."""
        try:
            difficulty = self.difficulty_var.get()
            
            # Initialize detector first
            self.detector.set_difficulty(difficulty)
            
            # Then set controller difficulty (which can now use the initialized detector)
            self.controller.set_difficulty(difficulty)
            
            # Initialize solver with board dimensions
            rows, cols = self.detector.get_board_dimensions()
            self.solver = MinesweeperSolver(rows, cols)
            
            self.status_var.set(f"Difficulty set to {difficulty.title()} ({rows}x{cols} grid)")
            messagebox.showinfo("Success", f"Difficulty set to {difficulty.title()}")
            
        except Exception as e:
            error_msg = f"Failed to set difficulty: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def _test_coordinates(self):
        """Test coordinate system by moving mouse to board positions."""
        try:
            if not self.solver:
                messagebox.showwarning("No Difficulty Set", 
                                     "Please set difficulty first.")
                return
            
            self.status_var.set("Testing coordinates... Watch your mouse!")
            messagebox.showinfo("Coordinate Test", 
                              "Watch your mouse move to test coordinates. This will take about 30 seconds.")
            
            # Run test in a separate thread
            test_thread = threading.Thread(target=self._run_coordinate_test)
            test_thread.daemon = True
            test_thread.start()
            
        except Exception as e:
            error_msg = f"Failed to test coordinates: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def _run_coordinate_test(self):
        """Run coordinate test in background thread."""
        try:
            self.controller.test_coordinates()
            self.root.after(0, lambda: self.status_var.set("Coordinate test completed"))
            self.root.after(0, lambda: messagebox.showinfo("Test Complete", 
                                "Coordinate test completed. Check the logs for details."))
        except Exception as e:
            error_msg = f"Coordinate test failed: {str(e)}"
            self.logger.error(error_msg)
            self.root.after(0, lambda: self.status_var.set("Coordinate test failed"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
    
    def _get_mouse_position(self):
        """Get current mouse position for debugging."""
        try:
            import pyautogui
            x, y = pyautogui.position()
            messagebox.showinfo("Mouse Position", f"Current mouse position: ({x}, {y})")
            self.logger.info(f"Current mouse position: ({x}, {y})")
        except Exception as e:
            error_msg = f"Failed to get mouse position: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def _start_solver(self):
        """Start the solver in a separate thread."""
        if self.is_running:
            messagebox.showwarning("Already Running", 
                                 "The solver is already running.")
            return
        
        if not self.solver:
            messagebox.showwarning("No Difficulty Set", 
                                 "Please set difficulty first.")
            return
        
        # Update UI
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("Starting solver...")
        self.progress_var.set(0)
        self.is_running = True
        
        # Start solver thread
        self.solver_thread = threading.Thread(target=self._run_solver)
        self.solver_thread.daemon = True
        self.solver_thread.start()
    
    def _run_solver(self):
        """Run the solver (called in separate thread)."""
        try:
            self._update_status("Initializing solver...")
            self._update_progress(10)
            
            # Capture and analyze initial board state
            self._update_status("Capturing initial board state...")
            board_image = self.detector.capture_board()
            board_state = self.detector.analyze_board(board_image)
            
            # Check if board is fresh and make initial click if needed
            if self.detector.is_board_fresh(board_state):
                self._update_status("Fresh board detected. Starting new game...")
                
                # Start a completely new game by clicking the smiley face
                self.controller.start_new_game()
                time.sleep(1)  # Wait for new game to start
                
                # Now make the initial center click to begin the game
                self._update_status("Making initial center click...")
                rows, cols = self.detector.get_board_dimensions()
                center_row, center_col = rows // 2, cols // 2
                self.controller.click_cell(center_row, center_col)
                time.sleep(1)  # Wait for board to update
                
                # Re-capture board after initial click
                self._update_status("Re-capturing board after initial click...")
                board_image = self.detector.capture_board()
                board_state = self.detector.analyze_board(board_image)
            else:
                self._update_status("Board already in progress. Continuing with current state...")
            
            self._update_status("Beginning solving loop...")
            self._update_progress(20)
            
            # Main solving loop
            move_count = 0
            max_moves = 1000  # Safety limit
            
            while self.is_running and move_count < max_moves:
                # Capture and analyze board
                self._update_status(f"Capturing board (move {move_count + 1})...")
                board_image = self.detector.capture_board()
                board_state = self.detector.analyze_board(board_image)
                
                # Save debug image occasionally
                if move_count % 10 == 0:
                    self.detector.save_debug_image(board_image, f"debug_board_{move_count}.png")
                
                # Log detailed board statistics
                stats = self.solver.get_board_statistics(board_state)
                self.solver.log_board_statistics(stats, move_count + 1)
                
                # Find safe moves and mines to flag
                safe_moves, mine_cells = self.solver.find_safe_moves(board_state)
                
                if not safe_moves and not mine_cells:
                    self._update_status("No safe moves or mines found. Game may be stuck or won.")
                    break
                
                # Execute flagging first (if any mines identified)
                if mine_cells:
                    self._update_status(f"Found {len(mine_cells)} mines to flag. Flagging...")
                    self.controller.flag_mines(mine_cells)
                    time.sleep(0.5)  # Wait for flags to be placed
                
                # Execute safe moves (if any)
                if safe_moves:
                    self._update_status(f"Found {len(safe_moves)} safe moves. Executing...")
                    self.controller.click_safe_cells(safe_moves)
                else:
                    self._update_status("No safe moves found this iteration.")
                
                move_count += len(safe_moves) + len(mine_cells)
                self._update_progress(min(20 + (move_count * 0.8), 95))
                
                # Small delay between moves
                time.sleep(0.5)
                
                # Check for win condition (no unopened cells left AND some revealed content)
                stats = self.solver.get_board_statistics(board_state)
                revealed_content = stats['revealed_numbers'] + stats['blank'] + stats['flagged']
                
                if stats['unopened'] == 0 and revealed_content > 0:
                    self._update_status("Game won! All cells revealed.")
                    break
                elif stats['unopened'] == 0 and revealed_content == 0:
                    self._update_status("Board appears empty - may need to restart game.")
                    break
            
            if move_count >= max_moves:
                self._update_status("Maximum moves reached. Stopping.")
            
            self._update_status("Solver completed successfully!")
            self._update_progress(100)
            self.root.after(0, lambda: messagebox.showinfo("Success", 
                f"Solver completed! Made {move_count} moves."))
                
        except Exception as e:
            error_msg = f"Error running solver: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._update_status("Error occurred")
            self._update_progress(0)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        
        finally:
            # Reset UI
            self.root.after(0, self._reset_ui)
    
    def _stop_solver(self):
        """Stop the solver."""
        if self.is_running:
            self.is_running = False
            self.status_var.set("Stopping solver...")
    
    def _reset_ui(self):
        """Reset the UI to initial state."""
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.is_running = False
        if self.status_var.get() == "Stopping solver...":
            self.status_var.set("Ready - Select difficulty and start solver")
            self.progress_var.set(0)
    
    def run(self):
        """
        Run the GUI.
        This method blocks until the window is closed.
        """
        self.root.mainloop()
    
    def show_error(self, message: str):
        """Show an error message."""
        messagebox.showerror("Error", message)
    
    def show_info(self, message: str):
        """Show an info message."""
        messagebox.showinfo("Info", message)
    
    def update_status(self, message: str):
        """Update the status label."""
        self.status_var.set(message)
    
    def _update_status(self, message: str):
        """Internal method to update status from background thread."""
        # This method is called from the game controller thread
        # Use root.after to safely update GUI from background thread
        self.root.after(0, lambda: self.update_status(message))
    
    def update_progress(self, value: float):
        """Update the progress bar (0-100)."""
        self.progress_var.set(value)
    
    def _update_progress(self, value: float):
        """Internal method to update progress from background thread."""
        self.root.after(0, lambda: self.update_progress(value))
    
    def destroy(self):
        """Destroy the GUI."""
        self.root.destroy()
