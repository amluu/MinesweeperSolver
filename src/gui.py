import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
import time
from typing import Optional, Callable
try:
    import keyboard  # For global hotkeys
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
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
        self.root.geometry("300x475")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)  # Keep window on top
        
        # Bind ESC key to stop solver (works when GUI has focus)
        self.root.bind('<Escape>', lambda e: self._stop_solver())
        
        # Set up global ESC hotkey if keyboard module is available
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.add_hotkey('esc', self._stop_solver)
                self.global_hotkey_enabled = True
                self.logger.info("Global ESC hotkey enabled")
            except Exception as e:
                self.logger.warning(f"Could not set global ESC hotkey: {e}")
                self.global_hotkey_enabled = False
        else:
            self.global_hotkey_enabled = False
            self.logger.info("Keyboard module not available - using local ESC binding only")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Google Minesweeper Solver", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Status frame (moved to top)
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.status_var = tk.StringVar(value="Select difficulty and start solver")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, wraplength=250)
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, 
                                          maximum=100, length=230)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Game Settings frame (moved to middle)
        difficulty_frame = ttk.LabelFrame(main_frame, text="Game Settings", padding="10")
        difficulty_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(difficulty_frame, text="Difficulty:").grid(row=0, column=0, padx=(0, 10))
        
        self.difficulty_var = tk.StringVar(value="medium")
        self.difficulty_combo = ttk.Combobox(difficulty_frame, textvariable=self.difficulty_var,
                                           values=["easy", "medium", "hard"], state="readonly", width=14)
        self.difficulty_combo.grid(row=0, column=1, padx=(0, 15))
        
        # No Flag Mode checkbox on a new row
        self.no_flag_mode = tk.BooleanVar(value=False)
        self.no_flag_checkbox = ttk.Checkbutton(difficulty_frame, text="No Flag Mode", 
                                               variable=self.no_flag_mode)
        self.no_flag_checkbox.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Probabilistic Mode checkbox
        self.probabilistic_mode = tk.BooleanVar(value=False)
        self.probabilistic_checkbox = ttk.Checkbutton(difficulty_frame, text="Probabilistic Mode", 
                                                     variable=self.probabilistic_mode)
        self.probabilistic_checkbox.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                                text="Make sure Google Minesweeper is open \nand stays on screen!",
                                justify=tk.LEFT)
        instructions.grid(row=3, column=0, columnspan=3, pady=(0, 20))
        
        # Control buttons frame (moved to bottom)
        control_frame = ttk.LabelFrame(main_frame, text="Solver Control", padding="10")
        control_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.start_btn = ttk.Button(control_frame, text="Start Solver", 
                                   command=self._start_solver)
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", 
                                  command=self._stop_solver, state="disabled")
        self.stop_btn.grid(row=0, column=1)
        
        # Stop instructions
        if self.global_hotkey_enabled:
            esc_text = "Press ESC to stop the solver (works anywhere)."
        else:
            esc_text = "Select this window and press ESC to stop."
        
        stop_instructions = ttk.Label(main_frame, text=esc_text, justify=tk.LEFT)
        stop_instructions.grid(row=5, column=0, columnspan=3, pady=(0, 0))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(0, weight=1)
    
    
    def _start_solver(self):
        """Start the solver in a separate thread."""
        if self.is_running:
            messagebox.showwarning("Already Running", 
                                 "The solver is already running.")
            return
        
        # Initialize difficulty and solver automatically
        try:
            difficulty = self.difficulty_var.get()
            
            # Initialize detector first
            self.detector.set_difficulty(difficulty)
            
            # Then set controller difficulty (which can now use the initialized detector)
            self.controller.set_difficulty(difficulty)
            
            # Initialize solver with board dimensions and difficulty
            rows, cols = self.detector.get_board_dimensions()
            self.solver = MinesweeperSolver(rows, cols, difficulty)
            
            # Set probabilistic mode
            self.solver.set_probabilistic_mode(self.probabilistic_mode.get())
            
            self.status_var.set(f"Initialized {difficulty.title()} ({rows}x{cols} grid)")
            
        except Exception as e:
            error_msg = f"Failed to initialize difficulty: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
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
                
                # Reset state manager for new game
                self.solver.reset_state()
                
                # Start a completely new game by clicking the smiley face
                self.controller.start_new_game()
                time.sleep(0.5)  # Reduced wait for new game to start
                
                # Now make the initial center click to begin the game
                self._update_status("Making initial center click...")
                rows, cols = self.detector.get_board_dimensions()
                center_row, center_col = rows // 2, cols // 2
                self.controller.click_cell(center_row, center_col)
                time.sleep(0.5)  # Reduced wait for board to update
                
                # Re-capture board after initial click
                self._update_status("Re-capturing board...")
                board_image = self.detector.capture_board()
                board_state = self.detector.analyze_board(board_image)
            else:
                self._update_status("Continuing with current state...")
            
            self._update_status("Beginning solving loop...")
            self._update_progress(20)
            
            # Main solving loop
            move_count = 0
            max_moves = 1000  # Safety limit
            previous_board_states = []  # Track previous states to detect loops
            max_state_history = 5  # Keep last 5 states
            tab_focused_this_iteration = False  # Track if we've focused tab this iteration
            
            
            while self.is_running and move_count < max_moves:
                # Reset tab focus tracking for this iteration
                tab_focused_this_iteration = False
                
                # Capture and analyze board
                self._update_status(f"Capturing board (move {move_count + 1})...")
                board_image = self.detector.capture_board()
                board_state = self.detector.analyze_board(board_image)
                
                # PNG is now saved automatically with every OCR detection
                
                # Log detailed board statistics
                stats = self.solver.get_board_statistics(board_state)
                self.solver.log_board_statistics(stats, move_count + 1)
                
                # Check for loops by comparing with previous states
                # Use merged board state (includes internal flags) for loop detection
                merged_board = self.solver.get_state_manager().merge_with_ocr_board(board_state)
                board_state_key = tuple(sorted(merged_board.items()))
                if board_state_key in previous_board_states:
                    self._update_status("Detected loop in board state. Stopping...")
                    self.logger.warning("Loop detected in board state. Stopping solver...")
                    break
                
                # Update state history
                previous_board_states.append(board_state_key)
                if len(previous_board_states) > max_state_history:
                    previous_board_states.pop(0)
                
                # Find safe moves and mines to flag
                safe_moves, mine_cells = self.solver.find_safe_moves(board_state)
                
                if not safe_moves and not mine_cells:
                    self._update_status("No safe moves or mines found. Doing final OCR check...")
                    
                    # Final OCR check to see if any moves became available
                    self._update_status("Capturing final board state...")
                    final_board_image = self.detector.capture_board()
                    final_board_state = self.detector.analyze_board(final_board_image)
                    
                    # Check for moves one more time
                    final_safe_moves, final_mine_cells = self.solver.find_safe_moves(final_board_state)
                    
                    if final_safe_moves or final_mine_cells:
                        self._update_status(f"Final check found {len(final_safe_moves)} safe moves and {len(final_mine_cells)} mines!")
                        
                        # Execute final moves
                        if final_mine_cells or final_safe_moves:
                            # Check no-flag mode for final moves
                            final_flags_to_execute = final_mine_cells if not self.no_flag_mode.get() else []
                            
                            if final_mine_cells and final_safe_moves:
                                if self.no_flag_mode.get():
                                    self._update_status(f"Executing final safe moves: {len(final_safe_moves)} (mines not flagged due to no-flag mode)")
                                else:
                                    self._update_status(f"Executing final batch: {len(final_mine_cells)} mines and {len(final_safe_moves)} safe moves...")
                            elif final_mine_cells:
                                if self.no_flag_mode.get():
                                    self._update_status(f"Found {len(final_mine_cells)} final mines (not flagging due to no-flag mode)")
                                else:
                                    self._update_status(f"Executing final {len(final_mine_cells)} mine flags...")
                            else:
                                self._update_status(f"Executing final {len(final_safe_moves)} safe moves...")
                            
                            # Update state manager for final moves (including flags for internal tracking)
                            # Always update state manager for internal tracking, regardless of flag mode
                            for row, col in final_mine_cells:
                                self.solver.flag_cell(row, col)
                            for row, col in final_safe_moves:
                                self.solver.reveal_cell(row, col)
                            
                            # Execute final moves - only safe moves if no-flag mode is on
                            if final_safe_moves or final_flags_to_execute:
                                focus_tab = not tab_focused_this_iteration
                                self.controller.execute_batch_moves(final_safe_moves, final_flags_to_execute, focus_tab=focus_tab)
                                time.sleep(0.3)
                            
                            # Only count moves that were actually executed
                            move_count += len(final_safe_moves) + len(final_flags_to_execute)
                            self._update_progress(min(20 + (move_count * 0.8), 95))
                            
                            # Continue the loop for one more iteration
                            continue
                    else:
                        # Check if probabilistic mode is enabled
                        if self.solver.is_probabilistic_mode_enabled():
                            self._update_status("No certain moves found. Trying probabilistic move...")
                            
                            # Get the safest probabilistic move
                            probabilistic_move = self.solver.get_probabilistic_move(final_board_state)
                            
                            if probabilistic_move:
                                self._update_status(f"Making probabilistic move at {probabilistic_move}...")
                                
                                # Update state manager
                                self.solver.reveal_cell(probabilistic_move[0], probabilistic_move[1])
                                
                                # Execute the move
                                self.controller.execute_batch_moves([probabilistic_move], [], focus_tab=True)
                                time.sleep(0.3)
                                
                                move_count += 1
                                self._update_progress(min(20 + (move_count * 0.8), 95))
                                
                                # Continue the loop for one more iteration
                                continue
                            else:
                                self._update_status("No probabilistic moves available. Game may be stuck.")
                                break
                        else:
                            self._update_status("No certain moves found. Enable Probabilistic Mode to continue.")
                            # Show messagebox to user
                            self.root.after(0, lambda: messagebox.showinfo("No Certain Moves", 
                                "No certain moves found. Enable Probabilistic Mode to continue with best-guess moves."))
                            break
                
                # Execute moves efficiently using batch method
                if mine_cells or safe_moves:
                    # Check no-flag mode
                    flags_to_execute = mine_cells if not self.no_flag_mode.get() else []
                    
                    if mine_cells and safe_moves:
                        if self.no_flag_mode.get():
                            self._update_status(f"Found {len(mine_cells)} mines (not flagging) and {len(safe_moves)} safe moves. Executing safe moves...")
                        else:
                            self._update_status(f"Found {len(mine_cells)} mines and {len(safe_moves)} safe moves. Executing batch...")
                    elif mine_cells:
                        if self.no_flag_mode.get():
                            self._update_status(f"Found {len(mine_cells)} mines (not flagging due to no-flag mode)")
                        else:
                            self._update_status(f"Found {len(mine_cells)} mines to flag. Flagging...")
                    else:
                        self._update_status(f"Found {len(safe_moves)} safe moves. Executing...")
                    
                    # Update state manager for all moves (including flags for internal tracking)
                    # Always update state manager for internal tracking, regardless of flag mode
                    for row, col in mine_cells:
                        self.solver.flag_cell(row, col)
                    for row, col in safe_moves:
                        self.solver.reveal_cell(row, col)
                    
                    # Execute moves - only safe moves if no-flag mode is on
                    if safe_moves or flags_to_execute:
                        focus_tab = not tab_focused_this_iteration
                        self.controller.execute_batch_moves(safe_moves, flags_to_execute, focus_tab=focus_tab)
                        tab_focused_this_iteration = True  # Mark that we've focused tab this iteration
                        time.sleep(0.3)  # Reduced wait time after batch execution
                    
                    # Re-capture board after moves to ensure state is updated
                    self._update_status("Re-capturing board after moves...")
                    board_image = self.detector.capture_board()
                    board_state = self.detector.analyze_board(board_image)
                else:
                    # Check if probabilistic mode is enabled
                    if self.solver.is_probabilistic_mode_enabled():
                        self._update_status("No certain moves found. Trying probabilistic move...")
                        
                        # Get the safest probabilistic move
                        probabilistic_move = self.solver.get_probabilistic_move(board_state)
                        
                        if probabilistic_move:
                            self._update_status(f"Making probabilistic move at {probabilistic_move}...")
                            
                            # Update state manager
                            self.solver.reveal_cell(probabilistic_move[0], probabilistic_move[1])
                            
                            # Execute the move
                            self.controller.execute_batch_moves([probabilistic_move], [], focus_tab=True)
                            time.sleep(0.3)
                            
                            move_count += 1
                            self._update_progress(min(20 + (move_count * 0.8), 95))
                            
                            # Re-capture board after probabilistic move
                            self._update_status("Re-capturing board after probabilistic move...")
                            board_image = self.detector.capture_board()
                            board_state = self.detector.analyze_board(board_image)
                        else:
                            self._update_status("No probabilistic moves available. Game may be stuck.")
                    else:
                        self._update_status("No certain moves found this iteration.")
                
                # Only count moves that were actually executed
                move_count += len(safe_moves) + len(flags_to_execute)
                self._update_progress(min(20 + (move_count * 0.8), 95))
                
                # Reduced delay between moves for faster execution
                time.sleep(0.1)
                
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
        # Clean up global hotkey if it was set
        if hasattr(self, 'global_hotkey_enabled') and self.global_hotkey_enabled and KEYBOARD_AVAILABLE:
            try:
                keyboard.unhook_all_hotkeys()
            except Exception:
                pass
        self.root.destroy()
