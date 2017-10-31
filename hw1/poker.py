#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------
# Реализуйте функцию best_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. У каждой карты есть масть(suit) и
# ранг(rank)
# Масти: трефы(clubs, C), пики(spades, S), червы(hearts, H), бубны(diamonds, D)
# Ранги: 2, 3, 4, 5, 6, 7, 8, 9, 10 (ten, T), валет (jack, J), дама (queen, Q), король (king, K), туз (ace, A)
# Например: AS - туз пик (ace of spades), TH - дестяка черв (ten of hearts), 3C - тройка треф (three of clubs)

# Задание со *
# Реализуйте функцию best_wild_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. Кроме прочего в данном варианте "рука"
# может включать джокера. Джокеры могут заменить карту любой
# масти и ранга того же цвета, в колоде два джокерва.
# Черный джокер '?B' может быть использован в качестве треф
# или пик любого ранга, красный джокер '?R' - в качестве черв и бубен
# любого ранга.

# Одна функция уже реализована, сигнатуры и описания других даны.
# Вам наверняка пригодится itertools
# Можно свободно определять свои функции и т.п.
# -----------------

import itertools

RANK = '23456789TJQKA'
BLACK_JOKER = '?B'
RED_JOKER = '?R'
SUITS_JOKER = {BLACK_JOKER: "CS", RED_JOKER: "HD"}  # масти джокеров


def hand_rank(hand):
    """Возвращает значение определяющее ранг 'руки'"""
    ranks = card_ranks(hand)

    if straight(ranks) and flush(hand):
        return 8, max(ranks)
    elif kind(4, ranks):
        return 7, kind(4, ranks), kind(1, ranks)
    elif kind(3, ranks) and kind(2, ranks):
        return 6, kind(3, ranks), kind(2, ranks)
    elif flush(hand):
        return 5, ranks
    elif straight(ranks):
        return 4, max(ranks)
    elif kind(3, ranks):
        return 3, kind(3, ranks), ranks
    elif two_pair(ranks):
        return 2, two_pair(ranks), ranks
    elif kind(2, ranks):
        return 1, kind(2, ranks), ranks
    else:
        return 0, ranks


def card_ranks(hand):
    """Возвращает список рангов (его числовой эквивалент), отсортированный от большего к меньшему"""
    return sorted([RANK.index(rank) for rank, suit in hand], reverse=True)


def flush(hand):
    """Возвращает True, если все карты одной масти"""
    return len(set([suit for rank, suit in hand])) == 1


def straight(ranks):
    """Возвращает True, если отсортированные ранги формируют последовательность 5ти,
    где у 5ти карт ранги идут по порядку (стрит)"""

    _ranks = set(ranks)
    return len(_ranks) == 5 and max(_ranks) - min(_ranks) == 4


def kind(n, ranks):
    """Возвращает первый ранг, который n раз встречается в данной руке.
    Возвращает None, если ничего не найдено"""

    for rank in ranks:
        if ranks.count(rank) == n:
            return rank
    return None


def two_pair(ranks):
    """Если есть две пары, то возврщает два соответствующих ранга,
    иначе возвращает None"""

    pair_first = kind(2, ranks)
    pair_second = kind(2, list(reversed(ranks)))

    if pair_first is not None and pair_second is not None and pair_first != pair_second:
        return pair_first, pair_second
    return None


def best_hand(hand):
    """Из "руки" в 7 карт возвращает лучшую "руку" в 5 карт """
    return max(itertools.combinations(hand, 5), key=hand_rank)


red_cards = []
black_cards = []


def init_cards():
    """Заполняем массивы красных и черных карт"""
    for rank in RANK:
        for suit in 'HD':
            red_cards.append("{0}{1}".format(rank, suit))
        for suit in "CS":
            black_cards.append("{0}{1}".format(rank, suit))
    return


def best_wild_hand(hand):
    """best_hand но с джокерами"""

    # если нет джокеров
    if hand.count(BLACK_JOKER) == 0 and hand.count(RED_JOKER) == 0:
        return best_hand(hand)

    clear_hand = [card for card in hand if card not in SUITS_JOKER]  # читая рука без джокеров

    # массивы комбинаций красного и черного джокера исключая те, что есть вруке
    _black_cards = joker_combinations(BLACK_JOKER, clear_hand) if BLACK_JOKER in hand else None
    _red_cards = joker_combinations(RED_JOKER, clear_hand) if RED_JOKER in hand else None

    # объеденяем массивы в массив массивов по 2 эл или 1 если джокер 1
    if _black_cards and _red_cards:
        cards = [item for item in itertools.product(_black_cards, _red_cards)]
    elif _black_cards:
        cards = list(_black_cards)
    else:
        cards = list(_red_cards)

    # к чистым картам добавляем значение из массива массивов
    # possible_hands = itertools.product(clear_hand, cards)
    possible_hands = []
    for card in cards:
        new_hand = list(clear_hand)

        if BLACK_JOKER in hand and RED_JOKER in hand:
            new_hand.extend(card)
        else:
            new_hand.append(card)
        possible_hands.append(new_hand)

    # выбираем сильнейшую руку
    return max(set([best_hand(h) for h in possible_hands]), key=hand_rank)


def joker_combinations(joker, clear_hand):
    result = []
    for rank, suit in itertools.product(RANK, SUITS_JOKER[joker]):
        card = "{0}{1}".format(rank, suit)
        if card not in clear_hand:
            result.append(card)
    return result


def test_best_hand():
    print "test_best_hand..."
    assert (sorted(best_hand("6C 7C 8C 9C TC 5C JS".split())) == ['6C', '7C', '8C', '9C', 'TC'])
    assert (sorted(best_hand("TD TC TH 7C 7D 8C 8S".split())) == ['8C', '8S', 'TC', 'TD', 'TH'])
    assert (sorted(best_hand("JD TC TH 7C 7D 7S 7H".split())) == ['7C', '7D', '7H', '7S', 'JD'])
    print 'OK'


def test_best_wild_hand():
    print "test_best_wild_hand..."
    assert (sorted(best_wild_hand("6C 7C 8C 9C TC 5C ?B".split())) == ['7C', '8C', '9C', 'JC', 'TC'])
    assert (sorted(best_wild_hand("TD TC 5H 5C 7C ?R ?B".split())) == ['7C', 'TC', 'TD', 'TH', 'TS'])
    assert (sorted(best_wild_hand("JD TC TH 7C 7D 7S 7H".split())) == ['7C', '7D', '7H', '7S', 'JD'])
    print 'OK'


if __name__ == '__main__':
    test_best_hand()
    test_best_wild_hand()
