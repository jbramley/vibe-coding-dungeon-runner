import pygame
import random
import sys
import os


class Card:
    # Unicode suit symbols
    SUIT_SYMBOLS = {
        'Hearts': '♥',
        'Diamonds': '♦',
        'Clubs': '♣',
        'Spades': '♠'
    }

    # Suit colors
    SUIT_COLORS = {
        'Hearts': (255, 0, 0),    # Red
        'Diamonds': (255, 0, 0),  # Red
        'Clubs': (0, 0, 0),       # Black
        'Spades': (0, 0, 0)       # Black
    }

    # Convert numeric values to face card representations
    VALUE_NAMES = {
        1: 'A',
        11: 'J',
        12: 'Q',
        13: 'K'
    }

    def __init__(self, suit, value, x=0, y=0):
        self.suit = suit
        self.value = value
        self.x = x
        self.y = y
        self.is_face_up = False
        self.is_clickable = False
        self.rect = pygame.Rect(x, y, 70, 100)  # Standard card size

    def __repr__(self):
        return f"{self.get_value_name()} of {self.suit}"

    def get_value_name(self):
        # Convert numeric values to face card names
        return self.VALUE_NAMES.get(self.value, str(self.value))

    def draw(self, screen, value_font, suit_font):
        # Draw card background
        pygame.draw.rect(screen, (255, 255, 255), self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)  # Border

        if self.is_face_up:
            # Get suit color
            suit_color = self.SUIT_COLORS[self.suit]

            # Render card value
            value_text = self.get_value_name()
            value_render = value_font.render(value_text, True, suit_color)
            value_rect = value_render.get_rect(centerx=self.rect.left + 20,
                                               top=self.rect.top + 10)
            screen.blit(value_render, value_rect)

            # Render suit symbol
            suit_symbol = self.SUIT_SYMBOLS[self.suit]
            suit_text = suit_font.render(suit_symbol, True, suit_color)
            suit_rect = suit_text.get_rect(centerx=self.rect.right - 20,
                                           top=self.rect.top + 10)
            screen.blit(suit_text, suit_rect)

    def is_adjacent_to(self, other_card):
        # Create a list of adjacent values with wrapping
        adjacent_values = {
            1: [13, 2],  # Ace can be next to King or 2
            13: [12, 1],  # King can be next to Queen or Ace
        }

        # For other cards, standard +/- 1 adjacency
        for i in range(2, 13):
            adjacent_values[i] = [i - 1, i + 1]

        # Handle wrapping for 2 and 12
        adjacent_values[2].append(1)
        adjacent_values[12].append(13)

        return (other_card.value in adjacent_values.get(self.value, []))


class Deck:
    SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    VALUES = list(range(1, 14))  # Ace (1) to King (13)

    def __init__(self):
        self.cards = []
        self.create_deck()
        self.shuffle()

    def create_deck(self):
        self.cards = [
            Card(suit, value)
            for suit in self.SUITS
            for value in self.VALUES
        ]

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop() if self.cards else None


class TriPeaksBoard:
    def __init__(self, deck):
        self.deck = deck
        self.board_cards = []
        self.draw_pile = deck.cards.copy()  # Copy of remaining cards
        self.deck.cards.clear()  # Empty the original deck
        self.discard_pile = []
        self.active_card = None
        self.setup_board()

    def setup_board(self):
        # Updated Tri Peaks layout (1-2-3-4 cards)
        rows = [1, 2, 3, 4]  # Number of cards per row
        screen_width = 800
        card_width = 70
        card_height = 100
        card_margin_x = 10
        card_margin_y = 20  # Vertical spacing

        for row_index, num_cards in enumerate(rows):
            # Calculate starting x to center the row
            start_x = (screen_width - (num_cards * (card_width + card_margin_x))) / 2

            for col in range(num_cards):
                card = self.draw_pile.pop()
                # Position card
                card.x = start_x + col * (card_width + card_margin_x)
                card.y = 50 + row_index * (card_height - card_margin_y)
                card.rect.x = card.x
                card.rect.y = card.y
                card.row = row_index
                card.col = col

                # Face up the bottom row
                if row_index == len(rows) - 1:
                    card.is_face_up = True
                    card.is_clickable = True

                self.board_cards.append(card)

    def draw_card(self):
        # If draw pile is not empty, move top card to active card
        if self.draw_pile:
            self.active_card = self.draw_pile.pop()
            self.active_card.is_face_up = True
            return True
        return False

    def is_card_uncovered(self, card):
        # Check if card is uncovered by looking at cards in rows below
        for board_card in self.board_cards:
            # Check if this card is in a row above the current card
            if board_card.row > card.row:
                # Check if this card overlaps the current card horizontally
                if (board_card.row == card.row + 1 and
                        (board_card.col == card.col or board_card.col == card.col + 1)):
                    # If this overlapping card is still on the board, card is covered
                    if board_card.is_face_up:
                        return False
        return True

    def can_move_card(self, card):
        # Check if active card exists and is adjacent
        if (self.active_card and
                self.is_card_uncovered(card) and
                self.active_card.is_adjacent_to(card)):
            return True
        return False

    def move_card_to_active(self, card):
        # Move card to discard pile (active stack)
        self.discard_pile.append(card)

        # Remove card from board cards
        self.board_cards.remove(card)

        # Update active card
        self.active_card = card

        # Check and flip cards that are now uncovered
        self.check_uncovered_cards()

    def check_uncovered_cards(self):
        # Check each face-down card if it's now uncovered
        uncovered_cards = []
        for card in [c for c in self.board_cards if not c.is_face_up]:
            # Specific check for uncovered condition
            is_uncovered = True
            for overlapping_card in self.board_cards:
                # Check if there should be an overlapping card
                if (overlapping_card.row == card.row + 1 and
                        (overlapping_card.col == card.col or
                         overlapping_card.col == card.col + 1)):
                    # Card exists in the row below, so this card is covered
                    is_uncovered = False
                    break

            # If no overlapping cards found, the card is uncovered
            if is_uncovered:
                uncovered_cards.append(card)

        # Flip uncovered cards
        for card in uncovered_cards:
            card.is_face_up = True
            card.is_clickable = True


class Room:
    def __init__(self, deck):
        self.board = TriPeaksBoard(deck)
        self.difficulty = 1


class TriPeaksDungeonRunner:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Tri Peaks Dungeon Runner")

        # Try multiple font approaches
        try:
            # Try system fonts first
            self.value_font = pygame.font.SysFont("Arial", 36)
            self.suit_font = pygame.font.SysFont("Arial", 48)
        except:
            try:
                # Fallback to a default font
                self.value_font = pygame.font.Font(None, 36)
                self.suit_font = pygame.font.Font(None, 48)
            except Exception as e:
                print(f"Font loading error: {e}")
                pygame.quit()
                sys.exit()

        self.clock = pygame.time.Clock()
        self.deck = Deck()
        self.current_room = Room(self.deck)

        # Positions for draw pile and active card
        self.draw_pile_rect = pygame.Rect(100, 500, 70, 100)
        self.active_card_rect = pygame.Rect(200, 500, 70, 100)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check draw pile click
                if self.draw_pile_rect.collidepoint(event.pos):
                    self.current_room.board.draw_card()
                else:
                    # Check board cards click
                    self.handle_card_click(event.pos)

        return True

    def handle_card_click(self, pos):
        x, y = pos
        for card in self.current_room.board.board_cards:
            if card.is_clickable and card.rect.collidepoint(x, y):
                # Check if card can be moved to active stack
                if self.current_room.board.can_move_card(card):
                    self.current_room.board.move_card_to_active(card)
                    print(f"Moved {card}")

    def draw(self):
        # Clear the screen
        self.screen.fill((0, 100, 0))  # Dark green background

        # Draw all cards on the board
        for card in self.current_room.board.board_cards:
            card.draw(self.screen, self.value_font, self.suit_font)

        # Draw draw pile (face down)
        pygame.draw.rect(self.screen, (50, 50, 50), self.draw_pile_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), self.draw_pile_rect, 2)

        # Draw remaining draw pile count
        draw_count_font = pygame.font.SysFont("Arial", 24)
        draw_count_text = draw_count_font.render(
            str(len(self.current_room.board.draw_pile)),
            True, (255, 255, 255)
        )
        draw_count_rect = draw_count_text.get_rect(
            center=self.draw_pile_rect.center
        )
        self.screen.blit(draw_count_text, draw_count_rect)

        # Draw active card if exists
        if self.current_room.board.active_card:
            active_card = self.current_room.board.active_card
            active_card.x = self.active_card_rect.x
            active_card.y = self.active_card_rect.y
            active_card.rect.x = self.active_card_rect.x
            active_card.rect.y = self.active_card_rect.y
            active_card.draw(self.screen, self.value_font, self.suit_font)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.draw()
            self.clock.tick(60)  # 60 FPS

        pygame.quit()
        sys.exit()


# Main game execution
if __name__ == "__main__":
    game = TriPeaksDungeonRunner()
    game.run()