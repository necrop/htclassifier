
glosses = (
    ('eqxr', 'equals-type cross-reference'),
    ('comp', 'compound formation'),
    ('supe', 'superordinate term'),
    ('driv', 'parent word of derivative'),
    ('cfxr', 'cf.-type cross-reference'),
    ('syns', 'synonyms'),
    ('etym', 'etymology'),
    ('txny', 'taxonomic binomial/genus term'),
    ('nbor', 'neighbouring wordclass'),
    ('adeq', 'adjective equivalent of superordinate'),
    ('attb', 'adjective equivalent of noun'),
    ('lass', 'lemma used elsewhere as superordinate'),
    ('topc', 'estimated topic'),
)
gloss_map = {code: gloss for code, gloss in glosses}


def code_interpreter(code):
    try:
        return gloss_map[code]
    except KeyError:
        return code

def code_list():
    return glosses
