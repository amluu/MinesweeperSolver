import logging
from typing import Dict, Set, Tuple, Optional, List

class MinesweeperStateManager:
    """Manages the internal state of the minesweeper game independently of OCR detection."""
    
    def __init__(self, rows: int, cols: int):
        """Initialize the state manager with board dimensions."""
        self.rows = rows
        self.cols = cols
        self.logger = logging.getLogger(__name__)
        
        # Internal state tracking
        self.flagged_cells: Set[Tuple[int, int]] = set()
        self.revealed_cells: Set[Tuple[int, int]] = set()
        
        # Track moves made by the solver
        self.moves_made: List[Tuple[int, int, str]] = []  # (row, col, action)
        
        self.logger.info(f"Initialized state manager for {rows}x{cols} board")
    
    def flag_cell(self, row: int, col: int) -> bool:
        """Flag a cell as a mine. Returns True if successful, False if already flagged."""
        if (row, col) in self.flagged_cells:
            self.logger.warning(f"Attempted to flag already flagged cell ({row}, {col})")
            return False
        
        if (row, col) in self.revealed_cells:
            self.logger.warning(f"Attempted to flag already revealed cell ({row}, {col})")
            return False
        
        self.flagged_cells.add((row, col))
        self.moves_made.append((row, col, 'flag'))
        self.logger.info(f"Flagged cell ({row}, {col})")
        return True
    
    def reveal_cell(self, row: int, col: int) -> bool:
        """Mark a cell as revealed. Returns True if successful, False if already revealed."""
        if (row, col) in self.revealed_cells:
            self.logger.warning(f"Attempted to reveal already revealed cell ({row}, {col})")
            return False
        
        if (row, col) in self.flagged_cells:
            self.logger.warning(f"Attempted to reveal flagged cell ({row}, {col})")
            return False
        
        self.revealed_cells.add((row, col))
        self.moves_made.append((row, col, 'reveal'))
        self.logger.info(f"Revealed cell ({row}, {col})")
        return True
    
    def unflag_cell(self, row: int, col: int) -> bool:
        """Remove flag from a cell. Returns True if successful, False if not flagged."""
        if (row, col) not in self.flagged_cells:
            self.logger.warning(f"Attempted to unflag non-flagged cell ({row}, {col})")
            return False
        
        self.flagged_cells.remove((row, col))
        self.moves_made.append((row, col, 'unflag'))
        self.logger.info(f"Unflagged cell ({row}, {col})")
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
        """
        Merge OCR-detected board with internal state.
        OCR is only used for numbers, blanks, and unopened detection.
        Flags are ALWAYS taken from internal state, never from OCR.
        """
        merged_board = {}
        
        for row in range(self.rows):
            for col in range(self.cols):
                cell_pos = (row, col)
                
                # CRITICAL: Internal flag state ALWAYS takes precedence over OCR
                # Even if OCR sees a number where we have a flag, we keep the flag
                if self.is_flagged(row, col):
                    merged_board[cell_pos] = 'flag'
                    self.logger.debug(f"Cell ({row}, {col}): Using internal flag state, ignoring OCR: {ocr_board.get(cell_pos, 'none')}")
                    continue
                
                # Use OCR for revealed content (numbers, blanks) only for non-flagged cells
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
                        # For any other OCR content on non-flagged cells, use OCR
                        merged_board[cell_pos] = ocr_content
                else:
                    # No OCR data, use internal state
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
    
    def reset(self):
        """Reset the state manager for a new game."""
        self.flagged_cells.clear()
        self.revealed_cells.clear()
        self.moves_made.clear()
        self.logger.info("State manager reset for new game")
    
    def log_state(self):
        """Log the current state for debugging."""
        stats = self.get_board_statistics()
        self.logger.info(f"State Manager - Flagged: {stats['flagged']}, Revealed: {stats['revealed']}, Unopened: {stats['unopened']}")
        
        if self.flagged_cells:
            flagged_list = sorted(list(self.flagged_cells))
            self.logger.debug(f"Flagged cells: {flagged_list}")
    
    def validate_board_state(self, ocr_board: Dict[Tuple[int, int], str]) -> bool:
        """
        Validate that our internal state is consistent with OCR detection.
        Returns True if consistent, False if there are conflicts.
        """
        conflicts = []
        
        for row in range(self.rows):
            for col in range(self.cols):
                cell_pos = (row, col)
                
                # Check for conflicts between internal flag state and OCR
                if self.is_flagged(row, col):
                    if cell_pos in ocr_board and ocr_board[cell_pos] != 'flag':
                        conflicts.append(f"Cell ({row}, {col}): Internal=flag, OCR={ocr_board.get(cell_pos, 'unknown')}")
                
                # Check for conflicts with revealed cells
                if self.is_revealed(row, col):
                    if cell_pos in ocr_board:
                        ocr_content = ocr_board[cell_pos]
                        if ocr_content == 'unopened':
                            conflicts.append(f"Cell ({row}, {col}): Internal=revealed, OCR=unopened")
        
        if conflicts:
            self.logger.warning(f"Found {len(conflicts)} state conflicts:")
            for conflict in conflicts:
                self.logger.warning(f"  {conflict}")
            return False
        
        return True
