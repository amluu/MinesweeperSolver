from typing import Dict, List, Tuple, Set, Optional
import configparser
import os
from .state_manager import MinesweeperStateManager
from .csp_solver import MinesweeperCSPSolver

class MinesweeperSolver:
    """Handles the minesweeper solving logic."""
    
    def __init__(self, grid_rows: int, grid_cols: int, difficulty: str = 'medium'):
        """Initialize the solver with grid dimensions, difficulty, and mine count."""
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols
        self.difficulty = difficulty
        
        # Load mine count from config
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')
        config.read(config_path)
        self.max_mines = config.getint(f'difficulty.{difficulty}', 'mine_count', fallback=99)
        
        # Initialize state manager for tracking flags and revealed cells
        self.state_manager = MinesweeperStateManager(grid_rows, grid_cols, difficulty)
        
        # Initialize CSP solver
        self.csp_solver = MinesweeperCSPSolver(grid_rows, grid_cols, difficulty)
        
        # Probabilistic mode flag
        self.use_probabilistic = False
    
    def find_safe_moves(self, ocr_board: Dict[Tuple[int, int], str]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """
        Find safe moves and mine cells using three-tier approach:
        1. Deterministic logic
        2. CSP solver for advanced deduction
        3. Flag count check for endgame
        Returns a tuple of (safe_moves, mine_cells_to_flag).
        """
        # Merge OCR board with internal state
        merged_board = self.state_manager.merge_with_ocr_board(ocr_board)
        
        # Tier 1: Deterministic logic
        mine_cells = self._identify_mines(merged_board)
        safe_moves = self._find_safe_moves_from_board(merged_board)
        
        # If deterministic found moves, return them
        if safe_moves or mine_cells:
            return safe_moves, mine_cells
        
        # Tier 2: CSP solver for advanced deduction
        csp_mines, csp_safe = self.csp_solver.find_certain_cells(merged_board, self.state_manager)
        
        if csp_safe or csp_mines:
            return csp_safe, csp_mines
        
        # Tier 3: Flag count check for endgame
        if self.csp_solver.check_flag_count_completion(self.state_manager):
            all_safe = self._get_all_unopened_cells(merged_board)
            return all_safe, []
        
        # No moves found by any method
        return [], []
    
    def flag_cell(self, row: int, col: int) -> bool:
        """Flag a cell as a mine using the state manager."""
        return self.state_manager.flag_cell(row, col)
    
    def reveal_cell(self, row: int, col: int) -> bool:
        """Mark a cell as revealed using the state manager."""
        return self.state_manager.reveal_cell(row, col)
    
    def get_state_manager(self) -> MinesweeperStateManager:
        """Get the state manager for external access."""
        return self.state_manager
    
    def reset_state(self):
        """Reset the state manager for a new game."""
        self.state_manager.reset()
    
    def _identify_mines(self, board: Dict[Tuple[int, int], str]) -> List[Tuple[int, int]]:
        """
        Identify cells that are definitely mines based on current information.
        Returns a list of coordinates that should be flagged.
        """
        mine_cells = set()
        
        for (row, col), content in board.items():
            if content.isdigit():
                number = int(content)
                
                neighbors = self._get_neighbors(row, col)
                unopened_neighbors = [(nr, nc) for (nr, nc) in neighbors 
                                    if board.get((nr, nc)) == 'unopened']
                flagged_neighbors = sum(1 for (nr, nc) in neighbors 
                                      if self.state_manager.is_flagged(nr, nc))
                
                # If all unopened neighbors must be mines
                if len(unopened_neighbors) + flagged_neighbors == number:
                    for unopened in unopened_neighbors:
                        # Triple-check: ensure not flagged, not revealed, and not already in our set
                        if (not self.state_manager.is_flagged(unopened[0], unopened[1]) and 
                            not self.state_manager.is_revealed(unopened[0], unopened[1]) and
                            unopened not in mine_cells):
                            mine_cells.add(unopened)
        
        return list(mine_cells)
    
    def _find_safe_moves_from_board(self, board: Dict[Tuple[int, int], str]) -> List[Tuple[int, int]]:
        """
        Find safe moves from the current board state using advanced pattern recognition.
        """
        safe_moves = set()
        
        # First pass: Find obvious safe moves (all mines already flagged)
        for (row, col), content in board.items():
            if content.isdigit():
                number = int(content)
                
                neighbors = self._get_neighbors(row, col)
                unopened_neighbors = [(nr, nc) for (nr, nc) in neighbors 
                                    if board.get((nr, nc)) == 'unopened']
                flagged_neighbors = sum(1 for (nr, nc) in neighbors 
                                      if self.state_manager.is_flagged(nr, nc))
                
                
                # Case 1: All mines are already flagged, remaining neighbors are safe
                if flagged_neighbors == number:
                    for neighbor in unopened_neighbors:
                        current_state = board.get(neighbor)
                        # Ensure cell is unopened, not flagged, and not revealed
                        if (current_state == 'unopened' and 
                            not self.state_manager.is_flagged(neighbor[0], neighbor[1]) and
                            not self.state_manager.is_revealed(neighbor[0], neighbor[1]) and
                            neighbor not in safe_moves):
                            safe_moves.add(neighbor)
        
        # Second pass: Find safe moves using constraint satisfaction
        # Look for cells where we can determine safety through elimination
        for (row, col), content in board.items():
            if content.isdigit():
                number = int(content)
                
                neighbors = self._get_neighbors(row, col)
                unopened_neighbors = [(nr, nc) for (nr, nc) in neighbors 
                                    if board.get((nr, nc)) == 'unopened']
                flagged_neighbors = sum(1 for (nr, nc) in neighbors 
                                      if self.state_manager.is_flagged(nr, nc))
                
                # If we need exactly 1 mine and have exactly 1 unopened neighbor, it must be a mine
                # If we need 0 mines and have unopened neighbors, they must all be safe
                mines_needed = number - flagged_neighbors
                
                if mines_needed == 0 and len(unopened_neighbors) > 0:
                    # All unopened neighbors must be safe
                    for neighbor in unopened_neighbors:
                        current_state = board.get(neighbor)
                        # Ensure cell is unopened, not flagged, and not revealed
                        if (current_state == 'unopened' and 
                            not self.state_manager.is_flagged(neighbor[0], neighbor[1]) and
                            not self.state_manager.is_revealed(neighbor[0], neighbor[1]) and
                            neighbor not in safe_moves):
                            safe_moves.add(neighbor)
        
        return list(safe_moves)
    
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
    
    
    def get_board_statistics(self, board: Dict[Tuple[int, int], str]) -> Dict[str, int]:
        """Get statistics about the current board state using state manager data."""
        stats = {
            'total_cells': self.grid_rows * self.grid_cols,
            'unopened': 0,
            'flagged': 0,
            'revealed_numbers': 0,
            'blank': 0,
            'unknown': 0,
            'number_1': 0, 'number_2': 0, 'number_3': 0, 'number_4': 0,
            'number_5': 0, 'number_6': 0, 'number_7': 0, 'number_8': 0
        }
        
        for content in board.values():
            if content == 'unopened':
                stats['unopened'] += 1
            elif content == 'flag':
                stats['flagged'] += 1
            elif content.isdigit():
                stats['revealed_numbers'] += 1
                number = int(content)
                if 1 <= number <= 8:
                    stats[f'number_{number}'] += 1
            elif content == 'blank':
                stats['blank'] += 1
            else:
                stats['unknown'] += 1
        
        # Calculate percentage revealed
        revealed = stats['revealed_numbers'] + stats['blank'] + stats['flagged']
        stats['percent_revealed'] = round((revealed / stats['total_cells']) * 100, 1) if stats['total_cells'] > 0 else 0
        
        return stats
    
    
    def get_probabilistic_move(self, ocr_board: Dict[Tuple[int, int], str]) -> Optional[Tuple[int, int]]:
        """
        Get the safest probabilistic move (lowest mine probability).
        Returns the cell with the lowest probability of being a mine, or None if no unopened cells.
        """
        merged_board = self.state_manager.merge_with_ocr_board(ocr_board)
        
        # Get cell probabilities from CSP solver
        probabilities = self.csp_solver.get_cell_probabilities(merged_board, self.state_manager)
        
        if not probabilities:
            return None
        
        # Find cell with lowest mine probability
        safest_cell = min(probabilities.items(), key=lambda x: x[1])
        cell, probability = safest_cell
        
        return cell
    
    def set_probabilistic_mode(self, enabled: bool):
        """Enable or disable probabilistic mode."""
        self.use_probabilistic = enabled
    
    def is_probabilistic_mode_enabled(self) -> bool:
        """Check if probabilistic mode is enabled."""
        return self.use_probabilistic
    
    def _get_all_unopened_cells(self, board: Dict[Tuple[int, int], str]) -> List[Tuple[int, int]]:
        """Get all unopened cells that are not flagged or revealed."""
        unopened_cells = []
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                cell = (row, col)
                
                # Skip if flagged or revealed
                if self.state_manager.is_flagged(row, col) or self.state_manager.is_revealed(row, col):
                    continue
                
                # Skip if OCR shows it's revealed (numbers or blanks)
                if cell in board and (board[cell] in ['blank'] or board.get(cell, '').isdigit()):
                    continue
                
                unopened_cells.append(cell)
        
        return unopened_cells
