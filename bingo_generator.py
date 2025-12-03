import argparse
import random
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors


class BingoCard:
    """Represents a single bingo card with a 5x5 grid."""
    
    COLUMNS = ['B', 'I', 'N', 'G', 'O']
    RANGES = {
        'B': range(1, 16),
        'I': range(16, 31),
        'N': range(31, 46),
        'G': range(46, 61),
        'O': range(61, 76)
    }
    
    def __init__(self, card_id, player_name=None):
        self.card_id = card_id
        self.player_name = player_name
        self.grid = self._generate_grid()
    
    def _generate_grid(self):
        """Generate a 5x5 bingo grid with random numbers."""
        grid = []
        for col_idx, col_letter in enumerate(self.COLUMNS):
            column = random.sample(list(self.RANGES[col_letter]), 5)
            # Set center square (row 2, col 2) to FREE for N column
            if col_letter == 'N':
                column[2] = 'FREE'
            grid.append(column)
        
        # Transpose to get row-major format
        return [[grid[col_idx][row_idx] for col_idx in range(5)] for row_idx in range(5)]
    
    def get_grid_display(self):
        """Return grid as list of rows with column headers."""
        headers = self.COLUMNS
        return [headers] + self.grid
    
    def __eq__(self, other):
        """Check if two cards are identical."""
        if not isinstance(other, BingoCard):
            return False
        return self.grid == other.grid
    
    def __hash__(self):
        """Hash for uniqueness checking."""
        return hash(tuple(tuple(row) for row in self.grid))


def generate_unique_cards(num_participants, player_names=None):
    """Generate unique bingo cards for all participants."""
    cards = []
    seen_grids = set()
    attempts = 0
    max_attempts = num_participants * 100  # Prevent infinite loops
    
    while len(cards) < num_participants and attempts < max_attempts:
        card = BingoCard(len(cards) + 1, 
                        player_names[len(cards)] if player_names and len(cards) < len(player_names) else None)
        card_tuple = tuple(tuple(row) for row in card.grid)
        
        if card_tuple not in seen_grids:
            cards.append(card)
            seen_grids.add(card_tuple)
        
        attempts += 1
    
    if len(cards) < num_participants:
        print(f"Warning: Only generated {len(cards)} unique cards out of {num_participants} requested.")
    
    return cards


def generate_cards_with_guaranteed_winners(num_players, num_winners, num_draws, player_names=None):
    """
    Generate randomized bingo cards that guarantee winners.
    
    This function creates a set of bingo cards and generates random number draws
    that ensure exactly the specified number of winners within the given number of draws.
    
    Args:
        num_players: Total number of players/cards to generate
        num_winners: Number of winners to guarantee
        num_draws: Total number of random draws to make
        player_names: Optional list of player names
    
    Returns:
        Tuple of (cards, drawn_numbers) where:
        - cards: List of BingoCard objects
        - drawn_numbers: List of numbers drawn across all rounds
    """
    if num_winners > num_players:
        raise ValueError(f"Number of winners ({num_winners}) cannot exceed number of players ({num_players})")
    
    if num_draws < 1:
        raise ValueError(f"Number of draws must be at least 1")
    
    # First, generate unique cards for all players
    cards = []
    seen_grids = set()
    attempts = 0
    max_attempts = num_players * 100
    
    while len(cards) < num_players and attempts < max_attempts:
        card = BingoCard(len(cards) + 1,
                        player_names[len(cards)] if player_names and len(cards) < len(player_names) else None)
        card_tuple = tuple(tuple(row) for row in card.grid)
        
        if card_tuple not in seen_grids:
            cards.append(card)
            seen_grids.add(card_tuple)
        
        attempts += 1
    
    if len(cards) < num_players:
        print(f"Warning: Only generated {len(cards)} unique cards out of {num_players} requested.")
    
    # Generate draws that guarantee winners
    drawn_numbers = []
    winner_indices = set(random.sample(range(len(cards)), num_winners))
    
    # For each winning card, ensure at least one winning pattern is drawn
    for winner_idx in winner_indices:
        winning_card = cards[winner_idx]
        
        # Get all numbers from the card (excluding FREE)
        all_numbers = []
        for row in winning_card.grid:
            for cell in row:
                if cell != 'FREE':
                    all_numbers.append(cell)
        
        # Determine how many numbers to draw for this card to guarantee a win
        # For simplicity, we'll draw a complete row (5 numbers)
        if all_numbers:
            # Select a random row from the card
            row_idx = random.randint(0, 4)
            row_numbers = [winning_card.grid[row_idx][col_idx] 
                          for col_idx in range(5) 
                          if winning_card.grid[row_idx][col_idx] != 'FREE']
            
            # Add these row numbers to drawn numbers
            for num in row_numbers:
                if num not in drawn_numbers:
                    drawn_numbers.append(num)
    
    # Fill remaining draws with random numbers (1-75)
    while len(drawn_numbers) < num_draws:
        num = random.randint(1, 75)
        if num not in drawn_numbers:
            drawn_numbers.append(num)
    
    # Shuffle the drawn numbers to randomize the order
    random.shuffle(drawn_numbers)
    
    # Trim to exactly num_draws
    drawn_numbers = drawn_numbers[:num_draws]
    
    return cards, drawn_numbers


def create_pdf(cards, output_path, rounds, winners):
    """Create a PDF with 2x2 card layout per page."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Layout parameters
    margin = 0.1 * inch
    card_spacing = 0.05 * inch
    cards_per_row = 2
    cards_per_col = 2
    card_width = (width - 3 * margin - card_spacing) / cards_per_row
    card_height = (height - 3 * margin - card_spacing) / cards_per_col
    
    card_index = 0
    
    while card_index < len(cards):
        # Draw 4 cards (2x2 grid) per page
        for row in range(cards_per_col):
            for col in range(cards_per_row):
                if card_index >= len(cards):
                    break
                
                card = cards[card_index]
                x = margin + col * (card_width + card_spacing)
                y = height - margin - (row + 1) * (card_height + card_spacing)
                
                _draw_card(c, card, x, y, card_width, card_height)
                card_index += 1
        
        if card_index < len(cards):
            c.showPage()
    
    # Add metadata on last page
    c.setFont("Helvetica", 8)
    c.drawString(margin, margin * 0.5, 
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Rounds: {rounds} | Expected Winners: {winners} | Total Cards: {len(cards)}")
    
    c.save()
    print(f"PDF created: {output_path}")


def _draw_card(c, card, x, y, width, height):
    """Draw a single bingo card on the canvas."""
    cell_width = width / 5
    cell_height = height / 6  # Extra row for header
    
    # Card border
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(2)
    c.rect(x, y, width, height)
    
    # Card ID and player name
    c.setFont("Helvetica-Bold", 10)
    player_info = f"Card {card.card_id}"
    if card.player_name:
        player_info += f": {card.player_name}"
    c.drawString(x + 5, y + height - 12, player_info)
    
    # Draw header row (B, I, N, G, O)
    c.setFont("Helvetica-Bold", 9)
    header_y = y + height - cell_height
    for col_idx, header in enumerate(BingoCard.COLUMNS):
        cell_x = x + col_idx * cell_width
        c.rect(cell_x, header_y, cell_width, cell_height)
        c.drawCentredString(cell_x + cell_width / 2, header_y + cell_height / 2 - 3, header)
    
    # Draw grid cells
    c.setFont("Helvetica", 8)
    for row_idx, row in enumerate(card.grid):
        for col_idx, value in enumerate(row):
            cell_x = x + col_idx * cell_width
            cell_y = y + height - (row_idx + 2) * cell_height
            
            # Draw cell border
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.setLineWidth(0.5)
            c.rect(cell_x, cell_y, cell_width, cell_height)
            
            # Highlight FREE space
            if value == 'FREE':
                c.setFillColorRGB(0.9, 0.9, 0.9)
                c.rect(cell_x, cell_y, cell_width, cell_height, fill=1, stroke=0)
                c.setFillColorRGB(0, 0, 0)
                c.drawCentredString(cell_x + cell_width / 2, cell_y + cell_height / 2 - 2, 'FREE')
            else:
                c.drawCentredString(cell_x + cell_width / 2, cell_y + cell_height / 2 - 2, str(value))


def main():
    parser = argparse.ArgumentParser(description='Generate bingo cards as PDF with guaranteed winners')
    parser.add_argument('--players', type=int, required=True, help='Number of players')
    parser.add_argument('--winners', type=int, required=True, help='Number of guaranteed winners')
    parser.add_argument('--draws', type=int, required=True, help='Number of draws/rounds')
    parser.add_argument('--names', type=str, help='Comma-separated list of player names')
    parser.add_argument('--output', type=str, default='/Users/srikalimani/Workspace/Bingo/output', 
                       help='Output directory')
    
    args = parser.parse_args()
    
    player_names = None
    if args.names:
        player_names = [name.strip() for name in args.names.split(',')]
    
    print(f"Generating {args.players} bingo cards with {args.winners} guaranteed winners in {args.draws} draws...")
    cards, drawn_numbers = generate_cards_with_guaranteed_winners(args.players, args.winners, args.draws, player_names)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"bingo_cards_{args.players}players_{args.winners}winners_{args.draws}draws_{timestamp}.pdf"
    output_path = os.path.join(args.output, filename)
    
    create_pdf(cards, output_path, args.draws, args.winners)
    print(f"Successfully generated {len(cards)} unique bingo cards with {args.winners} guaranteed winners!")
    print(f"Numbers to draw (in order): {drawn_numbers}")


if __name__ == '__main__':
    main()
