
from django.contrib.auth.models import User
from ...models import Level2Class
from ..codeinterpreter import code_list

wordclasses = (
    ('any', 'any'),
    ('NN', 'noun'),
    ('JJ', 'adjective'),
    ('VB', 'verb'),
    ('RB', 'adverb'),
    ('PHRASE', 'phrase'),
    ('UH', 'interjection'),
)
sensetypes = (
    ('any', 'any'),
    ('main sense', 'main sense'),
    ('compound', 'compound'),
    ('phrase', 'phrase'),
    ('derivative', 'derivative'),
)
defstatus = (
    ('any', 'any'),
    ('defined', 'defined'),
    ('undefined', 'undefined'),
)
bayesmismatch = (
    ('any', 'any'),
    ('no', 'matched only'),
    ('yes', 'mismatched only'),
)
splitdefinition = (
    ('any', 'any'),
    ('no', 'no split definition'),
    ('yes', 'split definitions only'),
)
marking = (
    ('any', 'any'),
    ('c', 'correct'),
    ('p', 'partially correct'),
    ('i', 'incorrect'),
    ('n', 'not marked'),
)
delta = (
    ('any', 'any time'),
    ('10', 'in the last 10 minutes'),
    ('60', 'in the last hour'),
    ('360', 'in the last 6 hours'),
    ('1440', 'in the last 24 hours'),
    ('10080', 'in the last week'),
    ('40320', 'in the last month'),
)


class SearchForm(object):

    def __init__(self, store):
        self.store = store

    def lemma(self):
        return self.store.get('lemma', '')

    def headword(self):
        return self.store.get('headword', '')

    def includetopicalclassifications(self):
        return bool(self.store.get('includetopicalclassifications', False))

    def wordclass_options(self):
        if self.store.get('wordclass'):
            default = False
        else:
            default = True
        options = []
        for option in wordclasses:
            if (option[0] == self.store.get('wordclass') or
                (default and option[0] == 'any')):
                options.append((option[0], option[1], True))
            else:
                options.append((option[0], option[1], False))
        return options

    def branch_options(self):
        if self.store.get('branch'):
            default = False
        else:
            default = True
        lev2 = Level2Class.objects.filter(level=2, wordclass=None)
        lev2 = sorted(list(lev2), key=lambda c: c.breadcrumb())
        if default or self.store.get('branch') == 'any':
            options = [('any', 'any', True),]
        else:
            options = [('any', 'any', False),]
        for thesclass in lev2:
            if self.store.get('branch') == str(thesclass.id):
                options.append((thesclass.id, thesclass.breadcrumb(), True))
            else:
                options.append((thesclass.id, thesclass.breadcrumb(), False))
        return options

    def sensetype_options(self):
        if self.store.get('sensetype'):
            default = False
        else:
            default = True
        options = []
        for option in sensetypes:
            if (option[0] == self.store.get('sensetype') or
                (default and option[0] == 'any')):
                options.append((option[0], option[1], True))
            else:
                options.append((option[0], option[1], False))
        return options

    def defstatus_options(self):
        if self.store.get('defstatus'):
            default = False
        else:
            default = True
        options = []
        for option in defstatus:
            if (option[0] == self.store.get('defstatus') or
                (default and option[0] == 'any')):
                options.append((option[0], option[1], True))
            else:
                options.append((option[0], option[1], False))
        return options

    def bayesmismatch_options(self):
        if self.store.get('bayesmismatch'):
            default = False
        else:
            default = True
        options = []
        for option in bayesmismatch:
            if (option[0] == self.store.get('bayesmismatch') or
                (default and option[0] == 'any')):
                options.append((option[0], option[1], True))
            else:
                options.append((option[0], option[1], False))
        return options

    def splitdefinition_options(self):
        if self.store.get('splitdefinition'):
            default = False
        else:
            default = True
        options = []
        for option in splitdefinition:
            if (option[0] == self.store.get('splitdefinition') or
                (default and option[0] == 'any')):
                options.append((option[0], option[1], True))
            else:
                options.append((option[0], option[1], False))
        return options

    def reason_options(self):
        if self.store.get('reasoncode'):
            default = False
        else:
            default = True
        reasons = [('any', 'any')] + [(c, g) for c, g in code_list()]
        options = []
        for option in reasons:
            if (option[0] == self.store.get('reasoncode') or
                    (default and option[0] == 'any')):
                options.append((option[0], option[1], True))
            else:
                options.append((option[0], option[1], False))
        return options

    def marking_options(self):
        if self.store.get('marking'):
            default = False
        else:
            default = True
        options = []
        for option in marking:
            if (option[0] == self.store.get('marking') or
                    (default and option[0] == 'any')):
                options.append((option[0], option[1], True))
            else:
                options.append((option[0], option[1], False))
        return options

    def user_options(self):
        if self.store.get('editedby'):
            default = False
        else:
            default = True

        options = [('any', 'any', default),]
        for option in User.objects.all():
            label = '%s %s (%s)' % (option.first_name or '?',
                                    option.last_name or '?',
                                    option.username,)
            if option.username == self.store.get('editedby'):
                options.append((option.username, label, True))
            else:
                options.append((option.username, label, False))
        return options

    def delta_options(self):
        if self.store.get('delta'):
            default = False
        else:
            default = True
        options = []
        for option in delta:
            if (option[0] == self.store.get('delta') or
                    (default and option[0] == 'any')):
                options.append((option[0], option[1], True))
            else:
                options.append((option[0], option[1], False))
        return options
