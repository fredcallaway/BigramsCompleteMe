from .bigrams import Distribution

from collections import Counter
import re
import sublime_plugin
import sublime

class BigramsCompleteMe(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        location = locations[0]
        if not view.match_selector(location, 'text'):
            # only operate when editing a text field
            return

        prefix_region = view.word(location)
        previous_word = view.substr(view.word(prefix_region.begin() - 1))

        if prefix:
            completions = view.extract_completions(prefix)
        else:
            # exclude the current prefix from the bigram model
            all_text = view.substr(sublime.Region(0, view.size()))

            tokens = re.sub(r'[^\w\s\']', ' ', all_text).split()
            completions = list(set(tokens)) 

        following_words = get_words_following(view, previous_word)
        # don't count the prefix that you're currently typing
        if following_words[prefix]:
            following_words[prefix] -= 1

        distribution = Distribution(following_words)

        def probability(word):
            return distribution.probability(word)

        completions.sort(key=lambda c: - probability(c))
        matches = [('%s\t%2.2f' % (c, probability(c)), c) for c in completions]
        return matches


def get_words_following(view, word):
    pattern = r'\W%s\s' % word
    matches = view.find_all(pattern, sublime.IGNORECASE)
    followers = [view.substr(view.word(m.end() + 1))
                 for m in matches]
    return Counter(followers)