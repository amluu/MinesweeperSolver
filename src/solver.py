import logging
from typing import Dict, List, Tuple, Set

class MinesweeperSolver:
    """Handles the minesweeper solving logic."""
    
    def __init__(self, grid_rows: int, grid_cols: int):
        """Initialize the solver with grid dimensions."""
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols
        self.logger = logging.getLogger(__name__)
    
    def find_safe_moves(self, board: Dict[Tuple[int, int], str]) -> List[Tuple[int, int]]:
        """
        Find safe moves based on the current board state.
        Returns a list of coordinates that are safe to click.
        """
        # First pass: flag mines where we're certain
        self._flag_mines(board)
        
        # Second pass: find safe moves
        safe_moves = set()
        
        for (row, col), content in board.items():
            if content.isdigit():
                number = int(content)
                
                neighbors = self._get_neighbors(row, col)
                unopened_neighbors = [(nr, nc) for (nr, nc) in neighbors 
                                    if board.get((nr, nc)) == 'unopened']
                flagged_neighbors = sum(1 for (nr, nc) in neighbors 
                                      if board.get((nr, nc)) == 'flag')
                
                # If all remaining neighbors must be safe
                if flagged_neighbors == number:
                    for neighbor in unopened_neighbors:
                        if board.get(neighbor) != 'flag':
                            safe_moves.add(neighbor)
        
        return list(safe_moves) if safe_moves else []
    
    def _flag_mines(self, board: Dict[Tuple[int, int], str]) -> None:
        """
        Flag cells that are definitely mines based on current information.
        Modifies the board dictionary in place.
        """
        for (row, col), content in board.items():
            if content.isdigit():
                number = int(content)
                
                neighbors = self._get_neighbors(row, col)
                unopened_neighbors = [(nr, nc) for (nr, nc) in neighbors 
                                    if board.get((nr, nc)) == 'unopened']
                flagged_neighbors = sum(1 for (nr, nc) in neighbors 
                                      if board.get((nr, nc)) == 'flag')
                
                # If all unopened neighbors must be mines
                if len(unopened_neighbors) + flagged_neighbors == number:
                    for unopened in unopened_neighbors:
                        board[unopened] = 'flag'
                        self.logger.debug(f"Flagged mine at ({unopened[0]}, {unopened[1]})")
    
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
    
    def has_guaranteed_moves(self, board: Dict[Tuple[int, int], str]) -> bool:
        """Check if there are any guaranteed safe moves available."""
        return len(self.find_safe_moves(board)) > 0
    
    def get_board_statistics(self, board: Dict[Tuple[int, int], str]) -> Dict[str, int]:
        """Get statistics about the current board state."""
        stats = {
            'total_cells': len(board),
            'unopened': 0,
            'flagged': 0,
            'revealed_numbers': 0,
            'blank': 0,
            'unknown': 0
        }
        
        for content in board.values():
            if content == 'unopened':
                stats['unopened'] += 1
            elif content == 'flag':
                stats['flagged'] += 1
            elif content.isdigit():
                stats['revealed_numbers'] += 1
            elif content == 'blank':
                stats['blank'] += 1
            else:
                stats['unknown'] += 1
        
        return stats
