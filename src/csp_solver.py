import logging
from typing import Dict, List, Tuple, Set, Optional
from ortools.sat.python import cp_model

class MinesweeperCSPSolver:
    """Constraint solver for Minesweeper using OR-Tools CP-SAT."""
    
    # Standard Minesweeper mine counts
    MINE_COUNTS = {
        'easy': 10,
        'medium': 40, 
        'hard': 99
    }
    
    def __init__(self, grid_rows: int, grid_cols: int, difficulty: str):
        """Initialize the CSP solver with board dimensions and difficulty."""
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols
        self.difficulty = difficulty
        self.max_mines = self.MINE_COUNTS.get(difficulty, 99)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Initialized CSP solver for {grid_rows}x{grid_cols} board, {difficulty} difficulty, {self.max_mines} mines")
    
    def find_certain_cells(self, board: Dict[Tuple[int, int], str], state_manager) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """
        Find cells that are certain mines (1 in all solutions) or certain safe (0 in all solutions).
        Returns (certain_mines, certain_safe).
        """
        # Get unopened cells
        unopened_cells = self._get_unopened_cells(board, state_manager)
        
        if not unopened_cells:
            self.logger.debug("No unopened cells found for CSP solving")
            return [], []
        
        # Build constraint model
        model, cell_vars = self._build_constraint_model(board, state_manager, unopened_cells)
        
        if not model:
            self.logger.debug("Failed to build constraint model")
            return [], []
        
        # Find all solutions
        solutions = self._find_all_solutions(model, cell_vars, unopened_cells)
        
        if not solutions:
            self.logger.debug("No valid solutions found")
            return [], []
        
        self.logger.info(f"Found {len(solutions)} valid solutions")
        
        # Analyze solutions to find certain cells
        certain_mines = []
        certain_safe = []
        
        for cell in unopened_cells:
            cell_var = cell_vars[cell]
            mine_count = sum(1 for solution in solutions if solution[cell_var])
            
            if mine_count == len(solutions):
                # Cell is mine in ALL solutions
                certain_mines.append(cell)
                self.logger.info(f"CSP: Cell {cell} is CERTAIN MINE (in {mine_count}/{len(solutions)} solutions)")
            elif mine_count == 0:
                # Cell is safe in ALL solutions
                certain_safe.append(cell)
                self.logger.info(f"CSP: Cell {cell} is CERTAIN SAFE (in 0/{len(solutions)} solutions)")
        
        self.logger.info(f"CSP found {len(certain_mines)} certain mines and {len(certain_safe)} certain safe cells")
        return certain_mines, certain_safe
    
    def get_cell_probabilities(self, board: Dict[Tuple[int, int], str], state_manager) -> Dict[Tuple[int, int], float]:
        """
        Calculate the probability that each unopened cell contains a mine.
        Returns dict mapping cell coordinates to mine probability (0.0 to 1.0).
        """
        # Get unopened cells
        unopened_cells = self._get_unopened_cells(board, state_manager)
        
        if not unopened_cells:
            return {}
        
        # Build constraint model
        model, cell_vars = self._build_constraint_model(board, state_manager, unopened_cells)
        
        if not model:
            return {}
        
        # Find all solutions
        solutions = self._find_all_solutions(model, cell_vars, unopened_cells)
        
        if not solutions:
            return {}
        
        # Calculate probabilities
        probabilities = {}
        for cell in unopened_cells:
            cell_var = cell_vars[cell]
            mine_count = sum(1 for solution in solutions if solution[cell_var])
            probability = mine_count / len(solutions)
            probabilities[cell] = probability
        
        self.logger.info(f"Calculated probabilities for {len(unopened_cells)} cells based on {len(solutions)} solutions")
        return probabilities
    
    def _get_unopened_cells(self, board: Dict[Tuple[int, int], str], state_manager) -> List[Tuple[int, int]]:
        """Get all unopened cells that could potentially contain mines."""
        unopened_cells = []
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                cell = (row, col)
                
                # Skip if already flagged or revealed
                if state_manager.is_flagged(row, col) or state_manager.is_revealed(row, col):
                    continue
                
                # Skip if OCR shows it's revealed
                if cell in board and board[cell] in ['blank'] or (board.get(cell, '').isdigit()):
                    continue
                
                unopened_cells.append(cell)
        
        return unopened_cells
    
    def _build_constraint_model(self, board: Dict[Tuple[int, int], str], state_manager, unopened_cells: List[Tuple[int, int]]) -> Tuple[Optional[cp_model.CpModel], Optional[Dict]]:
        """Build the constraint satisfaction model."""
        if not unopened_cells:
            return None, None
        
        model = cp_model.CpModel()
        
        # Create boolean variables for each unopened cell (1 = mine, 0 = safe)
        cell_vars = {}
        for cell in unopened_cells:
            cell_vars[cell] = model.NewBoolVar(f'cell_{cell[0]}_{cell[1]}')
        
        # Add constraints for each numbered cell
        constraints_added = 0
        for (row, col), content in board.items():
            if content.isdigit():
                number = int(content)
                neighbors = self._get_neighbors(row, col)
                
                # Find unopened neighbors that are in our variable set
                unopened_neighbors = []
                flagged_neighbors = 0
                
                for neighbor in neighbors:
                    if neighbor in cell_vars:
                        unopened_neighbors.append(cell_vars[neighbor])
                    elif state_manager.is_flagged(neighbor[0], neighbor[1]):
                        flagged_neighbors += 1
                
                # Add constraint: sum of unopened neighbor mines + flagged neighbors = cell number
                if unopened_neighbors:
                    model.Add(sum(unopened_neighbors) + flagged_neighbors == number)
                    constraints_added += 1
                    self.logger.debug(f"Added constraint for cell ({row}, {col}): {len(unopened_neighbors)} unopened + {flagged_neighbors} flagged = {number}")
        
        # Add total mine count constraint
        total_flagged = len(state_manager.get_flagged_cells())
        remaining_mines = self.max_mines - total_flagged
        
        if remaining_mines >= 0 and unopened_cells:
            model.Add(sum(cell_vars.values()) == remaining_mines)
            constraints_added += 1
            self.logger.debug(f"Added total mine constraint: {remaining_mines} remaining mines")
        
        if constraints_added == 0:
            self.logger.debug("No constraints added - model not solvable")
            return None, None
        
        self.logger.debug(f"Built constraint model with {constraints_added} constraints and {len(unopened_cells)} variables")
        return model, cell_vars
    
    def _find_all_solutions(self, model: cp_model.CpModel, cell_vars: Dict, unopened_cells: List[Tuple[int, int]], max_solutions: int = 1000) -> List[Dict]:
        """Find all valid solutions to the constraint model."""
        solver = cp_model.CpSolver()
        
        # Set solver parameters for better performance
        solver.parameters.enumerate_all_solutions = True
        solver.parameters.max_time_in_seconds = 5.0  # 5 second timeout
        
        solutions = []
        
        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self, variables):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self.variables = variables
                self.solutions = []
            
            def on_solution_callback(self):
                # Store the solution
                solution = {}
                for cell, var in self.variables.items():
                    solution[var] = self.Value(var)
                self.solutions.append(solution)
                
                # Limit number of solutions to prevent memory issues
                if len(self.solutions) >= max_solutions:
                    self.StopSearch()
        
        collector = SolutionCollector(cell_vars)
        status = solver.SolveWithSolutionCallback(model, collector)
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            solutions = collector.solutions
            self.logger.debug(f"Found {len(solutions)} solutions in {solver.WallTime():.2f} seconds")
        else:
            self.logger.debug(f"Solver status: {status}")
        
        return solutions
    
    def _get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get all valid neighbors for a given cell."""
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if (dr, dc) != (0, 0):
                    nr, nc = row + dr, col + dc
                    if (0 <= nr < self.grid_rows and 0 <= nc < self.grid_cols):
                        neighbors.append((nr, nc))
        return neighbors
    
    def check_flag_count_completion(self, state_manager) -> bool:
        """
        Check if we've flagged the maximum number of mines.
        If so, all remaining unopened cells must be safe.
        """
        flagged_count = len(state_manager.get_flagged_cells())
        return flagged_count >= self.max_mines
