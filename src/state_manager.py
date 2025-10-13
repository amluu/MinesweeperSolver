from typing import Dict, Set, Tuple, Optional, List

class MinesweeperStateManager:
    """Manages the internal state of the minesweeper game."""
    
    def __init__(self, rows: int, cols: int, difficulty: str = 'medium'):
        """Initialize the state manager with board dimensions and difficulty."""
        self.rows = rows
        self.cols = cols
        self.difficulty = difficulty
        
        # Internal state tracking
        self.flagged_cells: Set[Tuple[int, int]] = set()
        self.revealed_cells: Set[Tuple[int, int]] = set()
        
        # Track moves made by the solver
        self.moves_made: List[Tuple[int, int, str]] = []  # (row, col, action)
    
    def flag_cell(self, row: int, col: int) -> bool:
        """Flag a cell as a mine. Returns True if successful, False if already flagged."""
        if (row, col) in self.flagged_cells:
            return False
        
        if (row, col) in self.revealed_cells:
            return False
        
        self.flagged_cells.add((row, col))
        self.moves_made.append((row, col, 'flag'))
        return True
    
    def reveal_cell(self, row: int, col: int) -> bool:
        """Mark a cell as revealed. Returns True if successful, False if already revealed."""
        if (row, col) in self.revealed_cells:
            return False
        
        if (row, col) in self.flagged_cells:
            return False
        
        self.revealed_cells.add((row, col))
        self.moves_made.append((row, col, 'reveal'))
        return True
    
    def is_flagged(self, row: int, col: int) -> bool:
        """Check if a cell is flagged."""
        return (row, col) in self.flagged_cells
    
    
    def is_revealed(self, row: int, col: int) -> bool:
        """Check if a cell is revealed."""
        return (row, col) in self.revealed_cells
    
    def get_cell_state(self, row: int, col: int) -> str:
        """Get the internal state of a cell."""
        if (row, col) in self.flagged_cells:
            return 'flag'
        elif (row, col) in self.revealed_cells:
            return 'revealed'
        else:
            return 'unopened'
    
    def get_flagged_cells(self) -> Set[Tuple[int, int]]:
        """Get all flagged cells."""
        return self.flagged_cells.copy()
    
    def get_revealed_cells(self) -> Set[Tuple[int, int]]:
        """Get all revealed cells."""
        return self.revealed_cells.copy()
    
    def get_unopened_cells(self) -> Set[Tuple[int, int]]:
        """Get all unopened cells."""
        all_cells = {(r, c) for r in range(self.rows) for c in range(self.cols)}
        return all_cells - self.flagged_cells - self.revealed_cells
    
    def merge_with_ocr_board(self, ocr_board: Dict[Tuple[int, int], str]) -> Dict[Tuple[int, int], str]:
        """Merge OCR-detected board with internal state."""
        merged_board = {}
        
        for row in range(self.rows):
            for col in range(self.cols):
                cell_pos = (row, col)
                
                # Keep flag from internal state
                if self.is_flagged(row, col):
                    merged_board[cell_pos] = 'flag'
                    continue
                
                # Use OCR for revealed content
                if cell_pos in ocr_board:
                    ocr_content = ocr_board[cell_pos]
                    
                    # Handle revealed content
                    if ocr_content.isdigit() or ocr_content == 'blank':
                        merged_board[cell_pos] = ocr_content
                        # Update our revealed state
                        if not self.is_revealed(row, col):
                            self.revealed_cells.add(cell_pos)
                    elif ocr_content == 'unopened':
                        merged_board[cell_pos] = 'unopened'
                    else:
                        # Use OCR
                        merged_board[cell_pos] = ocr_content
                else:
                    # Use internal state
                    merged_board[cell_pos] = self.get_cell_state(row, col)
        
        return merged_board
    
    def get_board_statistics(self) -> Dict[str, int]:
        """Get statistics about the current board state."""
        total_cells = self.rows * self.cols
        
        return {
            'total_cells': total_cells,
            'flagged': len(self.flagged_cells),
            'revealed': len(self.revealed_cells),
            'unopened': len(self.get_unopened_cells()),
            'moves_made': len(self.moves_made)
        }
    
    def get_difficulty(self) -> str:
        """Get the current difficulty level."""
        return self.difficulty
    
    def reset(self):
        """Reset the state manager for a new game."""
        self.flagged_cells.clear()
        self.revealed_cells.clear()
        self.moves_made.clear()
    
    def set_difficulty(self, difficulty: str):
        """Update the difficulty level."""
        if difficulty not in ['easy', 'medium', 'hard']:
            raise ValueError(f"Invalid difficulty: {difficulty}")
        self.difficulty = difficulty
    