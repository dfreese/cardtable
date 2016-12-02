#!/usr/bin/env python

from random import shuffle

class Card:
    allowed_val = (2, 3, 4, 5, 6, 7, 8, 9, 10, 'jack', 'queen', 'king', 'ace')
    allowed_suit = ('hearts', 'diamonds', 'spades', 'clubs')
    vals_serialize = ('value', 'suit', 'face_up')

    def __init__(self, value, suit, face_up=False):
        if value not in self.allowed_val:
            raise ValueError('Value of %s not allowed' % value)
        if suit not in self.allowed_suit:
            raise ValueError('Suit of %s not allowed' % suit)
        self.value = value
        self.suit = suit
        self.face_up = face_up

    def serialize(self):
        return {k: self.__dict__[k] for k in self.vals_serialize}

    def flip(self):
        self.face_up = not self.face_up

    def set_face_up(self, val):
        self.face_up = val

class Stack:
    def __init__(self):
        self.cards = []

    def __getitem__(self, key):
        return self.cards[key]

    def __iter__(self):
        for card in self.cards:
            yield card

    def serialize(self):
        return {'cards' : [c.serialize() for c in self.cards]}

    def clear(self):
        self.cards = []

    def push_card(self, card):
        if not isinstance(card, Card):
            raise TypeError('card was not of class Card')
        self.cards.append(card)

    def pop_card(self, idx=-1):
        return self.cards.pop(idx)

    def shuffle(self):
        shuffle(self.cards)

    def set_face_up(self, val):
        if (val is not False) and (val is not True):
            raise ValueError('Face up value should be boolean')
        for card in self.cards:
            card.set_face_up(val)

    def get_face_up(self):
        no_face_up = 0
        for card in self.cards:
            if card.face_up:
                no_face_up += 1
        if no_face_up >= len(self.cards):
            return True
        else:
            return False

    def flip(self):
        self.set_face_up(not self.get_face_up())

class Table:
    def __init__(self, size=8):
        self.size = size
        self.init_stacks()

    def init_stacks(self):
        self.stacks = []
        for ii in range(self.size):
            self.stacks.append(Stack())

    def __getitem__(self, key):
        return self.stacks[key]

    def __iter__(self):
        for stack in self.stacks:
            yield stack

    def clear(self):
        for stack in self.stacks:
            stack.clear()

    def push_stack(self, stack):
        if not isinstance(stack, Stack):
            raise TypeError('stack was not of class Stack')
        self.stacks.append(stack)

    def pop_stack(self, idx=-1):
        return self.stacks.pop(idx)

    def serialize(self):
        return {'stacks' : [s.serialize() for s in self.stacks]}

class Game:
    def __init__(self, no_hands=0, table_size=None, card_type=None):
        if table_size is None:
            self.table = Table()
        else:
            self.table = Table(table_size)
        if card_type is None:
            self.card_type = Card
        self.hands = []
        self.init_deck()
        self.table[0].shuffle()

    def init_deck(self):
        for suit in self.card_type.allowed_suit:
            for val in self.card_type.allowed_val:
                self.table[0].push_card(self.card_type(val, suit))

    def serialize(self):
        output = {}
        output['hands'] = [h.serialize() for h in self.hands]
        output['table'] = self.table.serialize()
        return output

    def push_hand(self):
        self.hands.append(Stack())

    def pop_hand(self, idx=-1):
        return self.hands.pop(idx)

    def interp_cmds(self, cmds, hand_idx):
        if 'moves' in cmds:
            for move in cmds['moves']:
                if ('from' not in move) and ('to' not in move):
                    raise ValueError('each move needs "to" and "from"')
                from_split = move['from'].split('c')
                from_card_id = int(from_split[-1])
                if from_split[0][0] == 's':
                    from_stack_id = int(from_split[0].split('s')[-1])
                    from_stack = self.table[from_stack_id]
                elif from_split[0][0] == 'h':
                    from_stack_id = int(from_split[0].split('h')[-1])
                    from_stack = self.hands[from_stack_id]

                # split in case the a card was dropped in an image, not a div
                to_split = move['to'].split('c')
                if to_split[0][0] == 's':
                    to_stack_idx = int(to_split[0].split('s')[-1])
                    to_stack = self.table[to_stack_idx]
                    to_hand_flag = False
                elif to_split[0][0] == 'h':
                    to_stack_idx = int(to_split[0].split('h')[-1])
                    to_stack = self.hands[to_stack_idx]
                    to_hand_flag = True

                card = from_stack.pop_card(from_card_id)
                if to_hand_flag:
                    card.set_face_up(True)
                to_stack.push_card(card)

        if 'flip' in cmds:
            if 'c' in cmds['flip']:
                flip_split = cmds['flip'].split('c')
                card_idx = int(flip_split[-1])
                if flip_split[0][0] == 's':
                    stack_idx = int(flip_split[0].split('s')[-1])
                    self.table[stack_idx][card_idx].flip()
                elif flip_split[0][0] == 'h':
                    stack_idx = int(flip_split[0].split('h')[-1])
                    self.hands[stack_idx][card_idx].flip()
                else:
                    pass
            else:
                if cmds['flip'][0] == 's':
                    stack_idx = int(cmds['flip'].split('s')[-1])
                    self.table[stack_idx].flip()
                elif cmds['flip'][0] == 'h':
                    stack_idx = int(cmds['flip'].split('h')[-1])
                    self.hands[stack_idx].flip()

        if 'shuffle' in cmds:
            shuffle_split = cmds['shuffle'].split('c')
            card_idx = int(shuffle_split[-1])
            if shuffle_split[0][0] == 's':
                stack_idx = int(shuffle_split[0].split('s')[-1])
                self.table[stack_idx].shuffle()
                self.table[stack_idx].set_face_up(False)
            elif shuffle_split[0][0] == 'h':
                pass

        if 'deal' in cmds:
            if 'id' not in cmds['deal'] or 'no_cards' not in cmds['deal']:
                # Probably should raise an error here
                return
            no_cards = int(cmds['deal']['no_cards'])
            id_split = cmds['deal']['id'].split('c')
            card_idx = int(id_split[-1])
            if id_split[0][0] == 's':
                stack_idx = int(id_split[0].split('s')[-1])
                # Check size and number of hands to see if it can be done.
                cards_req = len(self.hands) * no_cards
                if len(self.table[stack_idx].cards) < cards_req:
                    # Not enough cards, exit.
                    pass
                else:
                    stack = self.table[stack_idx]
                    hand_order = range(len(self.hands))
                    hand_order = hand_order[hand_idx:] + hand_order[:hand_idx]
                    for card_idx in range(no_cards):
                        for idx in hand_order:
                            hand = self.hands[idx]
                            hand.push_card(stack.pop_card())
            elif id_split[0][0] == 'h':
                pass
