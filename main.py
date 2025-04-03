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
        'Hearts': (255, 0, 0),  # Red
        'Diamonds': (255, 0, 0),  # Red
        'Clubs': (0, 0, 0),  # Black
        'Spades': (0, 0, 0)  # Black
    }

    # Convert numeric values to face card representations
    VALUE_NAMES = {
        1: 'A',
        11: 'J',
        12: 'Q',
        13: 'K'
    }

    # Damage values for each card
    DAMAGE_VALUES = {
        1: 1,  # Ace = 1
        2: 2,
        3: 3,
        4: 4,
        5: 5,
        6: 6,
        7: 7,
        8: 8,
        9: 9,
        10: 10,
        11: 10,  # Jack = 10
        12: 10,  # Queen = 10
        13: 10  # King = 10
    }

    def __init__(self, suit, value, x=0, y=0):
        self.suit = suit
        self.value = value
        self.x = x
        self.y = y
        self.is_face_up = False
        self.is_clickable = False
        # Smaller card size (was 70x100)
        self.rect = pygame.Rect(x, y, 55, 80)

    def __repr__(self):
        return f"{self.get_value_name()} of {self.suit}"

    def get_value_name(self):
        # Convert numeric values to face card names
        return self.VALUE_NAMES.get(self.value, str(self.value))

    def get_damage_value(self):
        # Return the damage value for this card
        return self.DAMAGE_VALUES.get(self.value, self.value)

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
            value_rect = value_render.get_rect(centerx=self.rect.left + 15,
                                               top=self.rect.top + 5)
            screen.blit(value_render, value_rect)

            # Render suit symbol
            suit_symbol = self.SUIT_SYMBOLS[self.suit]
            suit_text = suit_font.render(suit_symbol, True, suit_color)
            suit_rect = suit_text.get_rect(centerx=self.rect.right - 15,
                                           top=self.rect.top + 5)
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


class Enemy:
    def __init__(self, hp=50):
        self.max_hp = hp
        self.current_hp = hp
        # Position enemy higher on the screen above cards
        self.rect = pygame.Rect(400, 80, 80, 80)

    def take_damage(self, amount):
        self.current_hp -= amount
        if self.current_hp < 0:
            self.current_hp = 0
        return self.current_hp <= 0  # Return True if enemy is defeated

    def draw(self, screen, font):
        # Draw enemy as a circle
        pygame.draw.circle(screen, (200, 50, 50), self.rect.center, 40)
        pygame.draw.circle(screen, (150, 0, 0), self.rect.center, 40, 3)

        # Draw HP text
        hp_text = font.render(f"{self.current_hp}/{self.max_hp} HP", True, (255, 255, 255))
        hp_rect = hp_text.get_rect(center=self.rect.center)
        screen.blit(hp_text, hp_rect)

        # Draw HP bar
        bar_width = 120
        bar_height = 15
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.bottom + 10

        # Background bar (empty)
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))

        # HP bar (filled)
        fill_width = int(bar_width * (self.current_hp / self.max_hp))
        pygame.draw.rect(screen, (50, 200, 50), (bar_x, bar_y, fill_width, bar_height))

        # Border
        pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 2)


class TriPeaksBoard:
    def __init__(self, deck):
        self.deck = deck
        self.board_cards = []
        self.draw_pile = deck.cards.copy()  # Copy of remaining cards
        self.deck.cards.clear()  # Empty the original deck
        self.discard_pile = []
        self.active_card = None
        self.enemy = Enemy(50)  # Create an enemy with 50 HP
        self.damage_animation = None  # For showing damage numbers
        self.damage_timer = 0
        self.setup_board()

    def setup_board(self):
        # Updated Tri Peaks layout (1-2-3-4 cards)
        rows = [1, 2, 3, 4]  # Number of cards per row
        screen_width = 800
        card_width = 55  # Smaller card width (was 70)
        card_height = 80  # Smaller card height (was 100)
        card_margin_x = 8  # Smaller margin (was 10)
        card_margin_y = 15  # Smaller vertical spacing (was 20)

        # Start cards lower on the screen to make room for enemy
        start_y = 180  # Increased from 50 to 180

        for row_index, num_cards in enumerate(rows):
            # Calculate starting x to center the row
            start_x = (screen_width - (num_cards * (card_width + card_margin_x))) / 2

            for col in range(num_cards):
                card = self.draw_pile.pop()
                # Position card
                card.x = start_x + col * (card_width + card_margin_x)
                card.y = start_y + row_index * (card_height - card_margin_y)
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

        # Apply damage to enemy based on card value
        damage = card.get_damage_value()
        is_defeated = self.enemy.take_damage(damage)

        # Set damage animation
        self.damage_animation = {
            "damage": damage,
            "x": self.enemy.rect.centerx,
            "y": self.enemy.rect.centery - 50,
            "color": (255, 50, 50)
        }
        self.damage_timer = 60  # Show damage for 1 second (60 frames)

        # Print debug info
        print(f"Moved {card} - Dealt {damage} damage - Enemy HP: {self.enemy.current_hp}")

        # Check if enemy is defeated
        if is_defeated:
            print("Enemy defeated!")

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
            # Try system fonts first - smaller font sizes
            self.value_font = pygame.font.SysFont("Arial", 28)  # Was 36
            self.suit_font = pygame.font.SysFont("Arial", 36)  # Was 48
            self.ui_font = pygame.font.SysFont("Arial", 24)
            self.damage_font = pygame.font.SysFont("Arial", 36)
        except:
            try:
                # Fallback to a default font
                self.value_font = pygame.font.Font(None, 28)
                self.suit_font = pygame.font.Font(None, 36)
                self.ui_font = pygame.font.Font(None, 24)
                self.damage_font = pygame.font.Font(None, 36)
            except Exception as e:
                print(f"Font loading error: {e}")
                pygame.quit()
                sys.exit()

        self.clock = pygame.time.Clock()
        self.deck = Deck()
        self.current_room = Room(self.deck)

        # Positions for draw pile and active card - updated for smaller cards
        self.draw_pile_rect = pygame.Rect(100, 500, 55, 80)
        self.active_card_rect = pygame.Rect(180, 500, 55, 80)

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

    def draw(self):
        # Clear the screen
        self.screen.fill((0, 100, 0))  # Dark green background

        # Draw enemy
        self.current_room.board.enemy.draw(self.screen, self.ui_font)

        # Draw damage animation if active
        if self.current_room.board.damage_animation and self.current_room.board.damage_timer > 0:
            damage_info = self.current_room.board.damage_animation
            damage_text = self.damage_font.render(f"-{damage_info['damage']}", True, damage_info['color'])
            damage_rect = damage_text.get_rect(center=(damage_info['x'], damage_info['y']))
            self.screen.blit(damage_text, damage_rect)

            # Update damage animation
            self.current_room.board.damage_timer -= 1
            if self.current_room.board.damage_timer <= 0:
                self.current_room.board.damage_animation = None

        # Draw all cards on the board
        for card in self.current_room.board.board_cards:
            card.draw(self.screen, self.value_font, self.suit_font)

        # Draw draw pile (face down)
        pygame.draw.rect(self.screen, (50, 50, 50), self.draw_pile_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), self.draw_pile_rect, 2)

        # Draw remaining draw pile count
        draw_count_text = self.ui_font.render(
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

        # Draw game state info
        if self.current_room.board.enemy.current_hp <= 0:
            victory_text = self.damage_font.render("VICTORY!", True, (255, 215, 0))
            victory_rect = victory_text.get_rect(center=(400, 300))
            self.screen.blit(victory_text, victory_rect)

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