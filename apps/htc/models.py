from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

OED_BASEURL = 'https://poed.uk.hub.oup.com/'
DICTBROWSER_URL = OED_BASEURL + 'dicbrowser/displayentry.jsp?'
THESBROWSER_URL = OED_BASEURL + 'thesbrowser/displaythes.jsp?'


class ThesaurusClassBase(models.Model):

    label = models.CharField(max_length=200, null=True)
    wordclass = models.CharField(max_length=20, null=True)
    breadcrumb = models.CharField(max_length=350)
    level = models.IntegerField(db_index=True)
    superordinate = models.ForeignKey('self', null=True)
    branchsize = models.IntegerField()
    sortcode = models.IntegerField()

    class Meta:
        ordering = ['sortcode']
        abstract = True

    def __eq__(self, other):
        return self.id == other.id

    def ancestors(self):
        """
        Return a list of ancestor classes in ascending order,
        beginning with self.

        Note that that the present class is included as the first element
        of the list
        """
        ancestor_list = [self,]
        if self.superordinate is not None:
            ancestor_list.extend(self.superordinate.ancestors())
        return ancestor_list

    def ancestor(self, level=1):
        """
        Return the ancestor class at a specified level (defaults to 1)
        """
        if self.level == level:
            return self
        for a in self.ancestors():
            if a.level == level:
                return a
        return None

    def level2_ancestor(self):
        return self.ancestor(level=2)

    def node_label(self):
        label_string = self.label or ''
        if self.wordclass:
            label_string += ' [' + self.wordclass + ']'
        return label_string.strip()

    def indent(self):
        return self.level * 2

    def breadcrumb_dynamic(self):
        """
        Build the breadcrumb dynamically (by iterating through the labels
        of the present class's ancestors) and return it (as a string).

        It should usually be sufficient to use the stored breadcrumb; but
        this might be useful if, for example, the taxonomy changes.
        """
        ancestors = reversed(self.ancestors())
        ancestor_strings = []
        found_wordclass = False
        for a in ancestors:
            label = a.label or ''
            if a.wordclass and not found_wordclass:
                ancestor_strings.append('%s [%s]' % (label, a.wordclass))
                found_wordclass = True
            else:
                ancestor_strings.append(label)
        return ' \u00bb '.join([a.strip() for a in ancestor_strings[1:] ])

    def indented(self):
        def recurse(node, val):
            if node.superordinate is not None:
                val += '\u00a0\u00a0\u00a0\u00a0'
                return recurse(node.superordinate, val)
            else:
                return val
        return recurse(self, '') + self.breadcrumb

    def oed_url(self):
        template = '%sclassid=%d'
        return template % (THESBROWSER_URL, self.id)

    def wordclass_penn(self):
        if self.wordclass == 'noun':
            return 'NN'
        elif self.wordclass == 'adjective':
            return 'JJ'
        elif self.wordclass == 'adverb':
            return 'RB'
        elif self.wordclass and self.wordclass.startswith('verb'):
            return 'VB'
        elif self.wordclass and self.wordclass.startswith('phr'):
            return 'PHRASE'
        else:
            return self.wordclass


class ThesaurusClass(ThesaurusClassBase):

    def siblings(self):
        if self.superordinate:
            return ThesaurusClass.objects.filter(superordinate__id=self.superordinate.id)
        else:
            return [self, ]

    def children(self):
        return ThesaurusClass.objects.filter(superordinate__id=self.id)

    def local_context(self):
        tree = list(reversed([a for a in self.ancestors() if a != self]))
        sibs = list(self.siblings())
        kids = list(self.children())
        for t in sibs:
            tree.append(t)
            if t == self:
                tree.extend(kids)
        return tree


class Level2Class(ThesaurusClassBase):
    """
    Identical to the main ThesaurusClass model, but intended to hold
    only classes at levels 1 and 2 (i.e. main branches).

    (Since these level-2 branches are used to filter results, we keep
    them in their own table - much smaller than the full taxonomy table -
    in order to improve performance.)
    """
    pass


class Sense(models.Model):

    lemma = models.CharField(max_length=100)
    lemmasort = models.CharField(max_length=100, db_index=True)
    wordclass = models.CharField(max_length=20, db_index=True)
    definition = models.CharField(max_length=200, null=True)
    refentry = models.IntegerField(db_index=True)
    refid = models.IntegerField()
    headword = models.CharField(max_length=50)
    headwordsort = models.CharField(max_length=50, db_index=True)
    status = models.CharField(max_length=1, db_index=True)
    subentrytype = models.CharField(max_length=20, db_index=True, null=True)
    undefined = models.BooleanField()
    sampleorder = models.IntegerField(db_index=True)

    bayes = models.ForeignKey(ThesaurusClass, null=True, related_name='+')
    bayesconfidence = models.IntegerField()
    bayesmismatch = models.BooleanField()

    thesclass1 = models.ForeignKey(ThesaurusClass, null=True)
    thesclass2 = models.ForeignKey(ThesaurusClass, null=True, related_name='+')
    thesclass3 = models.ForeignKey(ThesaurusClass, null=True, related_name='+')
    checkbox1 = models.CharField(max_length=1)
    checkbox2 = models.CharField(max_length=1)
    checkbox3 = models.CharField(max_length=1)
    checkstatus = models.CharField(max_length=1, db_index=True)
    user = models.ForeignKey(User, null=True)

    level2branch = models.ForeignKey(Level2Class, db_index=True, null=True)
    reasontext = models.CharField(max_length=200, null=True)
    reasoncode = models.CharField(max_length=4, null=True, db_index=True)
    splitdefinition = models.BooleanField()
    definition_supplement = models.CharField(max_length=150, null=True)

    comment = models.TextField(null=True)
    timestamp = models.DateTimeField(auto_now=True, null=True, db_index=True)

    class Meta:
        ordering = ['headwordsort', 'refentry', 'lemmasort', 'id']

    def __unicode__(self):
        return '%s (%d#eid%d)' % (self.lemma, self.refentry, self.refid)

    def get_absolute_url(self):
        return reverse('htc:sense', kwargs={'id': str(self.id)})

    def save_with_user(self, request):
        user = None
        try:
            request.user.username
        except AttributeError:
            pass
        else:
            if request.user.username:
                user = request.user
        self.user = user
        self.save()

    def oed_url(self):
        template = '%sidEntry=%d&isEnID=%d'
        return template % (DICTBROWSER_URL, self.refentry, self.refid)

    def oed_entry_url(self):
        template = '%sidEntry=%d&isEnID=0'
        return template % (DICTBROWSER_URL, self.refentry)

    def wordclass_readable(self):
        if self.wordclass == 'NN':
            return 'noun'
        elif self.wordclass == 'JJ':
            return 'adjective'
        elif self.wordclass == 'VB':
            return 'verb'
        elif self.wordclass == 'RB':
            return 'adverb'
        elif self.wordclass.startswith('PHR'):
            return 'phrase'
        elif self.wordclass is not None:
            return self.wordclass.lower()
        else:
            return '?'

    def status_readable(self):
        if self.status in ('1', 'c', 'p', 'i', 'u'):
            return 'classified'
        elif self.status == '0':
            return 'unclassified'
        elif self.status == 'n':
            return 'unclassified (intractable)'
        else:
            return '?'

    def thesclasses(self):
        def data_packet(i, c):
            thesclass, status = c
            allow_correct = (thesclass and thesclass.wordclass)
            return {'class': thesclass,
                    'status': status,
                    'count': i + 1,
                    'allow_correct': allow_correct}

        dataset = zip((self.thesclass1, self.thesclass2, self.thesclass3),
                      (self.checkbox1, self.checkbox2, self.checkbox3))
        classlist = [data_packet(i, c) for i, c in enumerate(dataset)]
        return [c for c in classlist if c['class'] and
                (c['count'] == 1 or c['class'].wordclass)]

    def live_thesclasses(self):
        return [c for c in self.thesclasses() if c['status'] in ('u', 'c', 'p')]

    def deprecated_thesclasses(self):
        return [c for c in self.thesclasses() if c['status'] in ('i',)]

    def username(self):
        if self.user:
            return self.user.username
        else:
            return 'anonymous'

    def user_fullname(self):
        if self.user:
            return (self.user.first_name or '?') + ' ' + (self.user.last_name or '?')
        else:
            return 'anonymous'

    def user_label(self):
        return '%s (%s)' % (self.user_fullname(), self.username())

    def comment_with_linebreaks(self):
        if self.comment:
            return self.comment.replace('\n', '<br/>')
        else:
            return ''

    def row_id(self):
        return 'row-%d' % self.id
