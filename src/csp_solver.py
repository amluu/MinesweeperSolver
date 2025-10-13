from typing import Dict, List, Tuple, Set, Optional
import configparser
import os
from ortools.sat.python import cp_model

class MinesweeperCSPSolver:
    """Constraint solver for Minesweeper using OR-Tools CP-SAT."""
    
    def __init__(self, grid_rows: int, grid_cols: int, difficulty: str):
        """Initialize the CSP solver with board dimensions and difficulty."""
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols
        self.difficulty = difficulty
        
        # Load mine count from config
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')
        config.read(config_path)
        self.max_mines = config.getint(f'difficulty.{difficulty}', 'mine_count', fallback=99)
    
    def find_certain_cells(
        self,
        board: Dict[Tuple[int, int], str],
        state_manager
    ) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """
        Find cells that are certain mines or certain safe using feasibility checks on a single model.
        Returns (certain_mines, certain_safe).
        """
        
        frontier_cells = self._get_frontier_cells(board, state_manager)
        if not frontier_cells:
            return [], []
        if len(frontier_cells) > 100:
            return [], []

        model, cell_vars = self._build_constraint_model(board, state_manager, frontier_cells)
        if not model:
            return [], []

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 1.0

        certain_mines: List[Tuple[int, int]] = []
        certain_safe: List[Tuple[int, int]] = []

        for cell in frontier_cells:
            v = cell_vars[cell]
            
            # Test if cell can be safe
            model_copy = model.Clone()
            model_copy.AddAssumption(v.Not())
            safe_status = solver.Solve(model_copy)
            
            # Test if cell can be a mine
            model_copy2 = model.Clone()
            model_copy2.AddAssumption(v)
            mine_status = solver.Solve(model_copy2)

            safe_feasible = safe_status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
            mine_feasible = mine_status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

            if not safe_feasible and mine_feasible:
                certain_mines.append(cell)
            elif not mine_feasible and safe_feasible:
                certain_safe.append(cell)
            elif not safe_feasible and not mine_feasible:
                pass

        if len(certain_mines) > 50 or len(certain_safe) > 50:
            return [], []

        return certain_mines, certain_safe
    
    def get_cell_probabilities(
        self,
        board: Dict[Tuple[int, int], str],
        state_manager
    ) -> Dict[Tuple[int, int], float]:
        """
        Calculate the probability that each frontier cell contains a mine using sampling.
        Returns dict mapping cell coordinates to mine probability (0.0 to 1.0).
        """
        frontier_cells = self._get_frontier_cells(board, state_manager)
        if not frontier_cells:
            return {}
        
        model, cell_vars = self._build_constraint_model(board, state_manager, frontier_cells)
        if not model:
            return {}
        
        solutions = self._find_all_solutions(model, cell_vars, frontier_cells, max_solutions=100)
        if not solutions:
            return {}
        
        probabilities: Dict[Tuple[int, int], float] = {}
        for cell in frontier_cells:
            var = cell_vars[cell]
            mine_count = sum(1 for sol in solutions if sol[var])
            probabilities[cell] = mine_count / len(solutions)
        
        return probabilities
    
    def _get_frontier_cells(
        self,
        board: Dict[Tuple[int, int], str],
        state_manager
    ) -> List[Tuple[int, int]]:
        """Get frontier cells (unopened cells that have numbered neighbors)."""
        frontier_cells: List[Tuple[int, int]] = []
        flagged_count = 0
        revealed_count = 0
        ocr_revealed_count = 0
        all_unopened_count = 0
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                cell = (row, col)
                
                if state_manager.is_flagged(row, col):
                    flagged_count += 1
                    continue
                if state_manager.is_revealed(row, col):
                    revealed_count += 1
                    continue
                
                if cell in board and (board[cell] in ['blank'] or board.get(cell, '').isdigit()):
                    ocr_revealed_count += 1
                    continue
                
                all_unopened_count += 1
                
                neighbors = self._get_neighbors(row, col)
                has_numbered_neighbor = any(
                    neighbor in board and board[neighbor].isdigit()
                    for neighbor in neighbors
                )
                if has_numbered_neighbor:
                    frontier_cells.append(cell)
        
        return frontier_cells
    
    def _get_unopened_cells(
        self,
        board: Dict[Tuple[int, int], str],
        state_manager
    ) -> List[Tuple[int, int]]:
        """Get all unopened cells that could potentially contain mines."""
        unopened_cells: List[Tuple[int, int]] = []
        flagged_count = 0
        revealed_count = 0
        ocr_revealed_count = 0
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                cell = (row, col)
                
                if state_manager.is_flagged(row, col):
                    flagged_count += 1
                    continue
                if state_manager.is_revealed(row, col):
                    revealed_count += 1
                    continue
                
                if cell in board and (board[cell] in ['blank'] or board.get(cell, '').isdigit()):
                    ocr_revealed_count += 1
                    continue
                
                unopened_cells.append(cell)
        
        return unopened_cells
    
    def _build_constraint_model(
        self,
        board: Dict[Tuple[int, int], str],
        state_manager,
        unopened_cells: List[Tuple[int, int]]
    ) -> Tuple[Optional[cp_model.CpModel], Optional[Dict]]:
        """Build the constraint satisfaction model over a given set of unopened cells (usually the frontier)."""
        if not unopened_cells:
            return None, None
        
        model = cp_model.CpModel()
        
        # Create boolean variables for each unopened cell (1 = mine, 0 = safe)
        cell_vars: Dict[Tuple[int, int], cp_model.IntVar] = {}
        for cell in unopened_cells:
            cell_vars[cell] = model.NewBoolVar(f'cell_{cell[0]}_{cell[1]}')
        
        constraints_added = 0
        
        # Number constraints: sum(unopened_neighbor_vars) + flagged_neighbors == number
        for (row, col), content in board.items():
            if isinstance(content, str) and content.isdigit():
                number = int(content)
                neighbors = self._get_neighbors(row, col)
                
                unopened_neighbor_vars: List[cp_model.IntVar] = []
                flagged_neighbors = 0
                
                for nr, nc in neighbors:
                    neighbor = (nr, nc)
                    if neighbor in cell_vars:
                        unopened_neighbor_vars.append(cell_vars[neighbor])
                    elif state_manager.is_flagged(nr, nc):
                        flagged_neighbors += 1
                
                if unopened_neighbor_vars:
                    model.Add(sum(unopened_neighbor_vars) + flagged_neighbors == number)
                    constraints_added += 1
                else:
                    pass
        
        # Global mine count constraint
        total_flagged = len(state_manager.get_flagged_cells())
        remaining_mines = self.max_mines - total_flagged
        all_unopened_cells = self._get_unopened_cells(board, state_manager)
        
        
        if constraints_added == 0:
            return None, None
        
        # If we're solving over ALL unopened cells, we can force exact remaining_mines.
        if remaining_mines >= 0 and len(unopened_cells) == len(all_unopened_cells) and len(all_unopened_cells) > 0:
            model.Add(sum(cell_vars.values()) == remaining_mines)
        else:
            # We're only solving a subset (e.g., frontier). Bound the total mines in this subset.
            max_frontier_mines = max(0, min(len(unopened_cells), remaining_mines))
            # Lower bound is 0 (implicit), but add explicit bounds for clarity
            model.Add(sum(cell_vars.values()) >= 0)
            model.Add(sum(cell_vars.values()) <= max_frontier_mines)
        
        return model, cell_vars
    
    def _find_all_solutions(
        self,
        model: cp_model.CpModel,
        cell_vars: Dict[Tuple[int, int], cp_model.IntVar],
        unopened_cells: List[Tuple[int, int]],
        max_solutions: int = 1000
    ) -> List[Dict]:
        """Find up to max_solutions valid solutions to the constraint model."""
        solver = cp_model.CpSolver()
        solver.parameters.enumerate_all_solutions = True
        solver.parameters.max_time_in_seconds = 5.0  # time cap
        
        solutions: List[Dict] = []
        
        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self, variables_dict):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self.variables_dict = variables_dict
                self.solutions: List[Dict] = []
            
            def on_solution_callback(self):
                sol = {}
                for _, var in self.variables_dict.items():
                    sol[var] = self.Value(var)
                self.solutions.append(sol)
                if len(self.solutions) >= max_solutions:
                    self.StopSearch()
        
        collector = SolutionCollector(cell_vars)
        status = solver.SolveWithSolutionCallback(model, collector)
        
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            solutions = collector.solutions
        else:
            solutions = []
        
        return solutions
    
    def _get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get all valid neighbors for a given cell."""
        neighbors: List[Tuple[int, int]] = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if (dr, dc) != (0, 0):
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.grid_rows and 0 <= nc < self.grid_cols:
                        neighbors.append((nr, nc))
        return neighbors
    
    def check_flag_count_completion(self, state_manager) -> bool:
        """
        Check if we've flagged the maximum number of mines.
        If so, all remaining unopened cells must be safe.
        """
        flagged_count = len(state_manager.get_flagged_cells())
        return flagged_count >= self.max_mines
