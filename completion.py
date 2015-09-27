from .bigrams import BigramModel

import re
import sublime_plugin
import sublime

class BigramsCompleteMe(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        location = locations[0]
        if not view.match_selector(location, 'text'):
            # only operate when editing a text field
            return

        # exclude the current prefix from the bigram model
        prefix_region = view.word(location)
        previous_word = view.substr(view.word(prefix_region.begin() - 1))
        before_region = sublime.Region(0, prefix_region.begin())
        after_region = sublime.Region(prefix_region.end(), view.size())
        all_text = view.substr(before_region) + view.substr(after_region)

        tokens = re.sub(r'[^\w\s]', '', all_text).split()

        if prefix:
            completions = view.extract_completions(prefix)
        else:
            completions = list(set(tokens)) 

        model = BigramModel(tokens, smoothing=False, track_rare=False)

        def probability(word):
            return model.probability(previous_word, word)

        completions.sort(key=lambda c: - probability(c))
        matches = [('%s\t%2.2f' % (c, probability(c)), c) for c in completions]
        return matches
