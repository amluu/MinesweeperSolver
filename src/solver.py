import logging
from typing import Dict, List, Tuple, Set

class MinesweeperSolver:
    """Handles the minesweeper solving logic."""
    
    def __init__(self, grid_rows: int, grid_cols: int):
        """Initialize the solver with grid dimensions."""
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols
        self.logger = logging.getLogger(__name__)
        # Enable debug logging for this session
        self.logger.setLevel(logging.DEBUG)
    
    def find_safe_moves(self, board: Dict[Tuple[int, int], str]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """
        Find safe moves and mine cells based on the current board state.
        Returns a tuple of (safe_moves, mine_cells_to_flag).
        """
        # Create a copy of the board to avoid modifying the original
        board_copy = board.copy()
        
        # First pass: identify mines where we're certain
        mine_cells = self._identify_mines(board_copy)
        
        # Second pass: find safe moves
        safe_moves = self._find_safe_moves_from_board(board_copy)
        
        return safe_moves, mine_cells
    
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
                                      if board.get((nr, nc)) == 'flag')
                
                # Debug logging
                self.logger.debug(f"Cell ({row}, {col}) has number {number}: {len(unopened_neighbors)} unopened, {flagged_neighbors} flagged")
                
                # If all unopened neighbors must be mines
                if len(unopened_neighbors) + flagged_neighbors == number:
                    for unopened in unopened_neighbors:
                        if board.get(unopened) == 'unopened':  # Only flag if not already flagged
                            mine_cells.add(unopened)
                            self.logger.info(f"Identified mine at ({unopened[0]}, {unopened[1]}) based on cell ({row}, {col}) with number {number}")
        
        self.logger.info(f"Total mines identified: {len(mine_cells)}")
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
                                      if board.get((nr, nc)) == 'flag')
                
                # Debug logging for safe moves
                self.logger.debug(f"Checking safe moves for cell ({row}, {col}) with number {number}: {len(unopened_neighbors)} unopened, {flagged_neighbors} flagged")
                
                # Case 1: All mines are already flagged, remaining neighbors are safe
                if flagged_neighbors == number:
                    for neighbor in unopened_neighbors:
                        if board.get(neighbor) == 'unopened':  # Only click if not already flagged
                            safe_moves.add(neighbor)
                            self.logger.info(f"Identified safe move at ({neighbor[0]}, {neighbor[1]}) - all mines flagged for cell ({row}, {col}) with number {number}")
        
        # Second pass: Find safe moves using constraint satisfaction
        # Look for cells where we can determine safety through elimination
        for (row, col), content in board.items():
            if content.isdigit():
                number = int(content)
                
                neighbors = self._get_neighbors(row, col)
                unopened_neighbors = [(nr, nc) for (nr, nc) in neighbors 
                                    if board.get((nr, nc)) == 'unopened']
                flagged_neighbors = sum(1 for (nr, nc) in neighbors 
                                      if board.get((nr, nc)) == 'flag')
                
                # If we need exactly 1 mine and have exactly 1 unopened neighbor, it must be a mine
                # If we need 0 mines and have unopened neighbors, they must all be safe
                mines_needed = number - flagged_neighbors
                
                if mines_needed == 0 and len(unopened_neighbors) > 0:
                    # All unopened neighbors must be safe
                    for neighbor in unopened_neighbors:
                        if board.get(neighbor) == 'unopened':
                            safe_moves.add(neighbor)
                            self.logger.info(f"Identified safe move at ({neighbor[0]}, {neighbor[1]}) - no mines needed for cell ({row}, {col}) with number {number}")
        
        self.logger.info(f"Total safe moves identified: {len(safe_moves)}")
        return list(safe_moves)
    
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
        """Check if there are any guaranteed safe moves or mines to flag available."""
        safe_moves, mine_cells = self.find_safe_moves(board)
        return len(safe_moves) > 0 or len(mine_cells) > 0
    
    def get_board_statistics(self, board: Dict[Tuple[int, int], str]) -> Dict[str, int]:
        """Get statistics about the current board state."""
        stats = {
            'total_cells': len(board),
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
                # Count individual numbers
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
    
    def log_board_statistics(self, stats: Dict[str, int], iteration: int = 0):
        """Log detailed board statistics for debugging."""
        self.logger.info(f"=== Board Statistics (Iteration {iteration}) ===")
        self.logger.info(f"Total cells: {stats['total_cells']}")
        self.logger.info(f"Unopened: {stats['unopened']}")
        self.logger.info(f"Revealed numbers: {stats['revealed_numbers']}")
        self.logger.info(f"Blank cells: {stats['blank']}")
        self.logger.info(f"Flagged: {stats['flagged']}")
        self.logger.info(f"Unknown: {stats['unknown']}")
        self.logger.info(f"Percent revealed: {stats['percent_revealed']}%")
        
        # Log individual number counts
        number_counts = []
        for i in range(1, 9):
            count = stats[f'number_{i}']
            if count > 0:
                number_counts.append(f"{i}: {count}")
        
        if number_counts:
            self.logger.info(f"Number breakdown: {', '.join(number_counts)}")
        
        self.logger.info("=" * 40)
