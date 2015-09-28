# BigramsCompleteMe
BigramsCompleteMe is a sublime text plugin that sorts autocompletion results by their probability given the previous word. In many cases, you can repeat an existing phrase such as "sublime text" with just the first letters of each word (e.g. `s`, `space`, `tab`, `t`, `space`, `tab`).

![Example usage](https://i.gyazo.com/05161b7d00b08d9f2427e3c20d655182.gif)

## Installation
    
    cd '~Library/Application Support/Sublime Text 3/Packages/'
    git clone https://github.com/fredcallaway/BigramsCompleteMe.git

## Caveats
At present, BigramsCompleteMe does not work with sublime's fuzzy autocomplete feature. One can implement fuzzy autocompletion by constructing a regular expression of a character list joined by `.*` e.g. `b.*c.*m` for BigramsCompleteMe. However, sublime text's autocompletion API does not respect the order of autocompletion suggestions when fuzzy matching. This is likely because sublime text trumps the plugin's sorting with its own fuzzy match sorting.

## Future

- Fuzzy completion by remapping tab to `insert_best_bigram_completion`. This will involve a fair ammount of code due to cycle through options, etc...
- Pretrained bigram models in addition to current-file bigrams.