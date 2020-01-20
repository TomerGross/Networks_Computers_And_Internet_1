__author__ = 'Tomer Gross'
__date__ = 'January 9th, 2020'

import socket
from _thread import *
import random
games = {}  # save all games that in progress by client's socket number
players_online = {}  # save all the clients connected to the server, used for debugging purposes only


class Game:

    def __init__(self):
        self._deck = Deck()  # game's deck
        self._deck.shuffle()  # shuffle the deck
        self._bets = []  # history of player's bets
        self._player_cards = []  # history of player's cards
        self._dealer_cards = []  # history of dealer's cards
        self._round_num = 1  # counts round number
        self._player_money = 0  # how much the player won or lost
        self._finish_game = 0  # flag to finish the game
        self._war_or_surrender = 0  # flag for war / surrender deceleration

    def get_deck(self):
        return self._deck

    def get_bets(self):
        return self._bets

    def get_player_cards(self):
        return self._player_cards

    def get_dealer_cards(self):
        return self._dealer_cards

    def get_round_num(self):
        return self._round_num

    def get_player_money(self):
        return self._player_money

    def get_finish_game(self):
        return self._finish_game

    def get_war_or_surrender(self):
        return self._war_or_surrender

    def set_war_or_surrender(self, wos):
        self._war_or_surrender = wos

    def set_first_card(self, fc):
        self._first_card = fc

    def set_player_cards(self, pc):
        self._player_cards = pc

    def set_finish_game(self, fg):
        self._finish_game = fg

    def inc_round(self):
        self._round_num += 1

    def player_won(self, bet):
        self._player_money += bet

    def player_lost(self, bet):
        self._player_money -= bet

    def take_dealer_card(self):
        card = self._deck.get_cards()[0]
        curr_deck = self._deck.get_cards()
        curr_deck.pop(0)  # take card from the deck
        self._deck.set_cards(curr_deck)
        self._dealer_cards.append(card)  # "deal" the card to the dealer
        return card

    def take_player_card(self):
        card = self._deck.get_cards()[0]
        curr_deck = self._deck.get_cards()
        curr_deck.pop(0)  # take card from the deck
        self._deck.set_cards(curr_deck)
        self._player_cards.append(card)  # "deal" the card to the player
        return card

    def get_dealer_card(self):
        return self._dealer_cards[-1]

    def get_player_card(self):
        return self._player_cards[-1]

    def add_last_bet(self, bet):
        self._bets.append(bet)

    def get_last_bet(self):
        return self._bets[-1]

    def discard_3_cards(self):
        curr_deck = self._deck.get_cards()
        curr_deck.pop(0)
        curr_deck.pop(0)
        curr_deck.pop(0)
        self._deck.set_cards(curr_deck)

    def update_game_progress(self, msg, c):

        if len(self.get_deck().get_cards()) > 1 and self.get_war_or_surrender() == 0:
            next_card = self.take_player_card()
            c.send((msg + "\n\nNext card: " + next_card.to_string()).encode())
        elif len(self.get_deck().get_cards()) > 1 and self.get_war_or_surrender() == 1:
            c.send(msg.encode())
        else:
            self.set_finish_game(1)
            amount = self.get_player_money()
            if amount >= 0:  # player has won in the game
                lose_win = "\n\nGame over\nPlayer won: " + str(amount) + "$\nPlayer is the winner!\nWould you like to play again? (yes/no)"
            else:  # player has lost in the game because the stack amount is negative
                lose_win = "\n\nGame over\nPlayer lost: " + str(-amount) + "$\nDealer is the winner!\nWould you like to play again? (yes/no)"
            c.send((msg + lose_win).encode())


class Deck:

    def __init__(self):

        self._cards = [] # holds the cards that currently left in the deck
        _card_value = 1

        for i in range(1, 14):  # for each card we will match a value (from 1 to 14) while Ace has the biggest value
            if i == 1:
                _card_value += 13

            self._cards.append(Card(_card_value, 'd'))
            self._cards.append(Card(_card_value, 'h'))
            self._cards.append(Card(_card_value, 's'))
            self._cards.append(Card(_card_value, 'c'))

            if i == 1:
                _card_value -= 13

            _card_value += 1

    def shuffle(self):
        random.shuffle(self._cards)

    def get_cards(self):
        return self._cards

    def set_cards(self, new_deck):
        self._cards = new_deck


class Card:

    def __init__(self, value, suit):
        self._value = value  # holds the value of the card (from 1 to 14)
        self._suit = suit  # holds the suit of the card (Clubs - c, Hearts - h, Spades - s, Diamonds - d)

    def to_string(self):  # represented the card value and its suit as a string
        value_to_card = {2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '10', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
        return value_to_card[self._value] + self._suit

    def get_value(self):
        return self._value

    def get_suit(self):
        return self._suit


# thread function
def threaded(c):
    global games
    while True:

        try:
            data = c.recv(1024).decode()  # data received from client
        except ConnectionResetError:
            break

        if not data:
            # in a case of some error
            break

        if games[c].get_finish_game() == 1 and (str(data) == "yes" or str(data) == "no"):  # game is over, check for player's rematch comment
            ans = str(data)
            if ans == "yes":  # player wants to play again
                del games[c]
                games[c] = Game()  # create a new game
                c.send(("First card: " + games[c].take_player_card().to_string()).encode())  # send first card
            else:  # player wants to leave
                del games[c]
                break

        elif str(data) == "status" and games[c].get_war_or_surrender() == 0 and games[c].get_finish_game() == 0:  # return player's status (if we are not waiting for w/s answer)
            amount = games[c].get_player_money()
            if amount >= 0:  # player is currently winning money
                lose_win = "Current round " + str(games[c].get_round_num()) + "\nPlayer won: " + str(amount) + "$"
            else:  # player is currently losing money
                lose_win = "Current round " + str(games[c].get_round_num()) + "\nPlayer lost: " + str(-amount) + "$"

            c.send(lose_win.encode())

        elif str(data) == "exit" and games[c].get_war_or_surrender() == 0 and games[c].get_finish_game() == 0:  # player wants to exit while game in progress (if we are not waiting for w/s answer)
            game_in_prog = games[c]
            amount = game_in_prog.get_player_money()

            if amount >= 0:
                c.send(("The game has ended on round " + str(game_in_prog.get_round_num()-1) + "!\nPlayer won: " + str(amount) + "$\nThanks for playing.").encode())
            else:
                c.send(("The game has ended on round " + str(game_in_prog.get_round_num()-1) + "!\nPlayer lost: " + str(-amount) + "$\nThanks for playing.").encode())
            del games[c]
            break

        elif str(data) == "s" and games[c].get_war_or_surrender() == 1 and games[c].get_finish_game() == 0:  # player surrendered
            game_in_prog = games[c]
            game_in_prog.set_war_or_surrender(0)
            part_won = game_in_prog.get_last_bet()/2
            msg = "Round " + str(game_in_prog.get_round_num()) + " tie breaker:\nPlayer surrendered!\n" + "The bet: " + str(game_in_prog.get_last_bet()) + "$\nPlayer won: " + str(part_won) + "$\nDealer won: " + str(part_won) + "$"
            game_in_prog.player_lost(part_won)
            game_in_prog.inc_round()
            game_in_prog.update_game_progress(msg, c)

        elif str(data) == "w" and games[c].get_war_or_surrender() == 1 and games[c].get_finish_game() == 0:  # player declared a war!
            game_in_prog = games[c]
            game_in_prog.set_war_or_surrender(0)
            msg = ""

            if len(game_in_prog.get_deck().get_cards()) < 5:
                msg = "Not enough cards for a war! this round canceled, no one won!"
                game_in_prog.inc_round()
                game_in_prog.update_game_progress(msg, c)
                continue

            game_in_prog.discard_3_cards()  # discard 3 cards before deal one card for both the player and the dealer

            original_bet = game_in_prog.get_last_bet()
            int_part_o, resident_o = divmod(original_bet, 1)
            new_bet = original_bet*2
            int_part_n, resident_n = divmod(new_bet, 1)

            if resident_o == 0:
                original_bet = int(original_bet)
            if resident_n == 0:
                new_bet = int(new_bet)

            dealer_card = game_in_prog.take_dealer_card()  # deal card to the dealer
            player_card = game_in_prog.take_player_card()  # deal card to the player

            if dealer_card.get_value() < player_card.get_value():  # player card is higher => player won in the war
                game_in_prog.player_won(new_bet/2)
                msg = "Round " + str(game_in_prog.get_round_num()) + " tie breaker:\nGoing to war!\n" + "3 cards were discarded\n" + "Original bet: " + str(original_bet) + "$\nNew bet: " + str(new_bet) + "$\nDealer’s card: " + dealer_card.to_string() + "\nPlayer’s card: " + player_card.to_string() + "\nPlayer won: " + str(original_bet) + "$"
                game_in_prog.inc_round()

            elif dealer_card.get_value() > player_card.get_value():  # player card is lower => dealer won in the war
                game_in_prog.player_lost(new_bet)
                msg = "Round " + str(game_in_prog.get_round_num()) + " tie breaker:\nGoing to war!\n" + "3 cards were discarded\n" + "Original bet: " + str(original_bet) + "$\nNew bet: " + str(new_bet) + "$\nDealer’s card: " + dealer_card.to_string() + "\nPlayer’s card: " + player_card.to_string() + "\nDealer won: " + str(new_bet) + "$"
                game_in_prog.inc_round()

            else:  # player card's value equals to the dealer card's value = player won in the war
                game_in_prog.player_won(new_bet)
                msg = "Round " + str(game_in_prog.get_round_num()) + " tie breaker:\nGoing to war!\n" + "3 cards were discarded\n" + "Original bet: " + str(original_bet) + "$\nNew bet: " + str(new_bet) + "$\nDealer’s card: " + dealer_card.to_string() + "\nPlayer’s card: " + player_card.to_string() + "\nPlayer won: " + str(new_bet) + "$"
                game_in_prog.inc_round()

            game_in_prog.update_game_progress(msg, c)

        elif games[c].get_war_or_surrender() == 0 and games[c].get_finish_game() == 0:
            try:
                game_in_prog = games[c]
                player_bet = float(data)
                int_part, resident = divmod(player_bet, 1)
                if resident == 0:  # for print purposes, if the number is actually integer
                    player_bet = int(player_bet)

                if player_bet <= 0:
                    c.send("Bet should be positive!".encode())
                    continue

                game_in_prog.add_last_bet(player_bet)  # remember player's bet
                dealer_card = game_in_prog.take_dealer_card()  # deal card to the dealer
                player_card = game_in_prog.get_player_card()  # deal card to the player

                if dealer_card.get_value() > player_card.get_value():  # player card is lower => dealer won in this round
                    msg = "The result of round :" + str(game_in_prog.get_round_num()) + "\nDealer won: " + str(player_bet) + "$\nDealer’s card: " + dealer_card.to_string() + "\nPlayer’s card: " + player_card.to_string()
                    game_in_prog.player_lost(player_bet)
                    game_in_prog.inc_round()

                elif dealer_card.get_value() < player_card.get_value():  # player card is higher => player won in this round
                    msg = "The result of round :" + str(game_in_prog.get_round_num()) + "\nPlayer won: " + str(player_bet) + "$\nDealer’s card: " + dealer_card.to_string() + "\nPlayer’s card: " + player_card.to_string()
                    game_in_prog.player_won(player_bet)
                    game_in_prog.inc_round()

                else:  # player card's value equals to the dealer card's value, let the player choose if surrender or go to a war
                    game_in_prog.set_war_or_surrender(1)
                    msg = "The result of round :" + str(game_in_prog.get_round_num()) + " is a tie!\n" + "Dealer’s card: " + dealer_card.to_string() + "\nPlayer’s card: " + player_card.to_string() + "\nDo you wish to surrender or go to war? [s/w]"

                game_in_prog.update_game_progress(msg, c)

            except ValueError:
                c.send("Incorrect function or incorrect bet type".encode())
        else:
            c.send("You should follow the instruction you got!".encode())

    # connection closed
    print("Disconnected: " + str(players_online[c][0]) + " : " + str(players_online[c][1]))
    del players_online[c]
    c.close()


def main():
    global players_online

    host = '0.0.0.0'  # bind to anyone
    port = 1005  # bind on specified port number

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("socket binded to port", port)
    s.listen()  # put the socket into listening mode
    print("socket is listening")

    while True:  # a forever loop until we manually wants to exit

        c, address = s.accept()  # establish connection with client
        players_online[c] = address

        if len(players_online) > 2:  # limit the amount of players that play at a time
            del players_online[c]
            c.send("Max amount of players at a time = 2. Try again later!".encode())
            c.close()
            continue

        print('Connected to :', address[0], ':', address[1])

        games[c] = Game()  # create a new game
        c.send(("First card: " + games[c].take_player_card().to_string()).encode())  # send first card

        start_new_thread(threaded, (c,))  # start a new thread and return its identifier

    s.close()


if __name__ == '__main__':
    main()
