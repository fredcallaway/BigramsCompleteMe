""""
Project 1 for CS 4740
Fred Callaway, Kang-Li Chen
"""
import bisect
from collections import Counter, defaultdict
from functools import lru_cache
import itertools
import math
import random
from typing import Dict

from .utils import cached_property


class CounterMatrix(object):
    """A two dimensional sparse matrix of counts with default 0 values."""
    def __init__(self, tokens, smooth=False):
        super(CounterMatrix, self).__init__()
        self.smooth = smooth

        self._dict = defaultdict(Counter)
        for i in range(len(tokens) - 1):
            self._dict[tokens[i]][tokens[i+1]] += 1

    def __len__(self):
        return len(self._dict)

    @cached_property()
    def count_counts(self):
        """The number of bigrams beginning with each token.

        value_counts[token][c] = number of bigrams beginning with token
        that were seen c times"""
        count_counts = defaultdict(Counter)
        for token, followers in self._dict.items():
            for f, count in followers.items():
                count_counts[token][count] += 1
            count_counts[token][0] = len(self) - sum(count_counts[token].values())
        return count_counts

    @cached_property()
    def good_turing_mapping(self, threshold=5) -> Dict[int, float]:
        """A dictionary mapping counts to good_turing smoothed counts."""
        total_count_counts = sum(self.count_counts.values(), Counter())
        def good_turing(c): 
            return (c+1) * (total_count_counts[c+1]) / total_count_counts.get(c, 1)
        gtm = {c: good_turing(c) for c in range(threshold)}
        return {k: v for k, v in gtm.items() if v > 0}  # can't have 0 counts

    @cached_property()
    def unigram_distribution(self):
        counts = {token: sum(follower.values()) 
                  for token, follower in self._dict.items()}
        return Distribution(counts)

    @lru_cache(maxsize=100000)  # caches 100,000 most recent results
    def distribution(self, token):
        """Returns next-token probability distribution for the given token.

        distributions('the').sample() gives words likely to occur after 'the'"""
        if token not in self._dict:
            token = 'UNKNOWN_TOKEN'
        if self.smooth:
            smoothing_dict = self.good_turing_mapping
            return Distribution(self._dict[token], smoothing_dict, self.count_counts[token])
        else:
            if self._dict[token]:
                return Distribution(self._dict[token])
            else:
                # no information -> use unigram
                return self.unigram_distribution


class Distribution(object):
    """A statistical distribution based on a dictionary of counts."""
    def __init__(self, counter, smoothing_dict={}, count_counts=None):
        assert counter
        self.counter = counter
        self.smoothing_dict = smoothing_dict

        # While finding the total, we also track each
        # intermediate total to make sampling faster.
        self._acc_totals = list(itertools.accumulate(counter.values()))
        self.total = self._acc_totals[-1]

        # Smoothing only applies to surprisal, not sampling so we maintain
        # a separate total that accounts for the smoothed counts
        if smoothing_dict:
            self.smooth_total = sum(smoothing_dict.get(count, count) * N_count 
                                    for count, N_count in count_counts.items())
        else:
            self.smooth_total = None

    def sample(self):
        """Returns an element from the distribution.

        Based on ideas from the following article:
        http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python"""
        rand = random.random() * self.total

        # Perform a binary search for index of highest number below rand.
        # index will thus be chosen with probability =
        # (self._acc_totals[i] - self._acc_totals[i-1]) / self.total
        index = bisect.bisect_right(self._acc_totals, rand)
        return list(self.counter.keys())[index]

    def probability(self, item):
        """The probability of an item being sampled."""
        count = self.counter.get(item, 0)
        if self.smoothing_dict:
            smooth_count = self.smoothing_dict.get(count, count)
            assert smooth_count > 0
            return smooth_count / self.smooth_total
        else:
            return count / self.total
    
    def surprisal(self, item):
        """The negative log probability of an item being sampled."""
        return - math.log(self.probability(item))


class BigramModel(object):
    """A bigram language model."""
    def __init__(self, tokens, smoothing=True, track_rare=True):
        self.tokens = tokens
        self.smoothing = smoothing
        self.track_rare = track_rare

        if track_rare:
            # first occurcence of a word is replaced with UNKNOWN_TOKEN
            seen_words = set()
            for i in range(len(self.tokens)):
                    word = self.tokens[i]
                    if word not in seen_words and word is not 'SENTENCE_BOUNDARY':
                        self.tokens[i] = 'UNKNOWN_TOKEN'
                    seen_words.add(word)


        self.cooccurrence_matrix = CounterMatrix(self.tokens, smooth=self.smoothing)

    def predict_next(self, token) -> str:
        """Returns a token from distribution of tokens that follow the given token."""
        return self.cooccurrence_matrix.distribution(token).sample()

    def surprisal(self, token: str, follower: str):
        """Returns the negative log probability of `follower` following `token`

        -log p(follower_i | token_{i-1})"""
        try:    
            dist = self.cooccurrence_matrix.distribution(token)
        except KeyError:
            dist = self.cooccurrence_matrix.distribution('UNKNOWN_TOKEN')
        return dist.surprisal(follower)

    def probability(self, token: str, follower: str):
        """Returns the probability of `follower` following `token`

        -log p(follower_i | token_{i-1})"""
        return self.cooccurrence_matrix.distribution(token).probability(follower)

    def generate_sentence(self, initial="") -> str:
        """Returns a randomly generated sentence.

        Optionally, the beginning of the sentence is given."""
        words = initial.split()
        if not words:
            words.append(self.predict_next('SENTENCE_BOUNDARY'))
        for i in range(30):  # 30 is max sentence length
            next_word = self.predict_next(words[-1])

            # avoid generating sentences with UNKNOWN_TOKEN
            while next_word == 'UNKNOWN_TOKEN':
                next_word = self.predict_next(words[-1])

            if next_word == 'SENTENCE_BOUNDARY':
                break
            else:
                words.append(next_word)
            if i == 29:
                words.append('...')

        return ' '.join(words) + '\n'

    def perplexity(self, tokens):
        """Average surprisal."""
        first_surprisal = self.surprisal('SENTENCE_BOUNDARY', tokens[0])
        total_surprisal = first_surprisal + sum(self.surprisal(tokens[i], tokens[i+1])
                                                for i in range(len(tokens) - 1))

        return math.exp(total_surprisal / (len(tokens)))