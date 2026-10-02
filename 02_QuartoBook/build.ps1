# Baut beide Sprachversionen.
# Deutsch -> _book/ , Englisch -> _book/en/
# Reihenfolge wichtig: DE zuerst (leert _book/), dann EN (leert nur _book/en/).
quarto render --profile de
quarto render --profile en
