import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from typing import Optional, Callable

class DifficultyGUI:
    """GUI for selecting difficulty and controlling the solver."""
    
    def __init__(self):
        """Initialize the GUI."""
        self.root = tk.Tk()
        self.selected_difficulty = None
        self.game_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        self.logger = logging.getLogger(__name__)
        
        self._setup_gui()
    
    def _setup_gui(self):
        """Set up the GUI components."""
        self.root.title("Minesweeper Solver")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Google Minesweeper Solver", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Difficulty selection frame
        diff_frame = ttk.LabelFrame(main_frame, text="Select Difficulty", padding="10")
        diff_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Difficulty buttons
        self.difficulty_var = tk.StringVar(value="")
        
        easy_btn = ttk.Radiobutton(diff_frame, text="Easy (8x10)", 
                                  variable=self.difficulty_var, value="easy")
        easy_btn.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        medium_btn = ttk.Radiobutton(diff_frame, text="Medium (14x18)", 
                                    variable=self.difficulty_var, value="medium")
        medium_btn.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        hard_btn = ttk.Radiobutton(diff_frame, text="Hard (20x24)", 
                                  variable=self.difficulty_var, value="hard")
        hard_btn.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=3, pady=(0, 20))
        
        self.start_btn = ttk.Button(control_frame, text="Start Solver", 
                                   command=self._start_solver)
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", 
                                  command=self._stop_solver, state="disabled")
        self.stop_btn.grid(row=0, column=1)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        self.status_var = tk.StringVar(value="Ready to start")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, 
                                          maximum=100, length=300)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(0, weight=1)
    
    def _start_solver(self):
        """Start the solver in a separate thread."""
        difficulty = self.difficulty_var.get()
        if not difficulty:
            messagebox.showwarning("No Difficulty Selected", 
                                 "Please select a difficulty level first.")
            return
        
        if self.is_running:
            messagebox.showwarning("Already Running", 
                                 "The solver is already running.")
            return
        
        # Update UI
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set(f"Starting {difficulty} solver...")
        self.progress_var.set(0)
        self.is_running = True
        
        # Start solver thread
        self.game_thread = threading.Thread(target=self._run_solver, args=(difficulty,))
        self.game_thread.daemon = True
        self.game_thread.start()
    
    def _run_solver(self, difficulty: str):
        """Run the solver (called in separate thread)."""
        try:
            self.status_var.set(f"Setting up browser for {difficulty}...")
            self.progress_var.set(20)
            
            # Import here to avoid circular imports
            from .game_controller import GameController
            
            # Create and run game controller
            controller = GameController(difficulty)
            
            self.status_var.set(f"Running {difficulty} solver...")
            self.progress_var.set(50)
            
            success = controller.run()
            
            if success:
                self.status_var.set(f"{difficulty.title()} game completed successfully!")
                self.progress_var.set(100)
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                    f"{difficulty.title()} game completed successfully!"))
            else:
                self.status_var.set(f"{difficulty.title()} game failed or stopped.")
                self.progress_var.set(0)
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"{difficulty.title()} game failed or stopped."))
                
        except Exception as e:
            error_msg = f"Error running solver: {str(e)}"
            self.logger.error(error_msg)
            self.status_var.set("Error occurred")
            self.progress_var.set(0)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        
        finally:
            # Reset UI
            self.root.after(0, self._reset_ui)
    
    def _stop_solver(self):
        """Stop the solver."""
        if self.is_running:
            self.is_running = False
            self.status_var.set("Stopping solver...")
            # Note: The actual stopping logic would need to be implemented
            # in the GameController to check for a stop flag
    
    def _reset_ui(self):
        """Reset the UI to initial state."""
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.is_running = False
        if self.status_var.get() == "Stopping solver...":
            self.status_var.set("Ready to start")
            self.progress_var.set(0)
    
    def run(self) -> str:
        """
        Run the GUI and return the selected difficulty.
        This method blocks until the window is closed.
        """
        self.root.mainloop()
        return self.selected_difficulty
    
    def show_error(self, message: str):
        """Show an error message."""
        messagebox.showerror("Error", message)
    
    def show_info(self, message: str):
        """Show an info message."""
        messagebox.showinfo("Info", message)
    
    def update_status(self, message: str):
        """Update the status label."""
        self.status_var.set(message)
    
    def update_progress(self, value: float):
        """Update the progress bar (0-100)."""
        self.progress_var.set(value)
    
    def destroy(self):
        """Destroy the GUI."""
        self.root.destroy()
