import re
import random
from datetime import datetime, timedelta

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.contrib.auth.models import User

from ...models import Sense, ThesaurusClass
from ..codeinterpreter import code_interpreter

results_per_page = 50

classified_statuses = ['1', 'c', 'p', 'i', 'u',]
classified_statuses_set = set(classified_statuses)


class ResultsList(object):

    def __init__(self, request, **kwargs):
        self.path = request.path
        self.req = request.GET
        self.args = kwargs

    def parameter_controls(self):
        """
        List of current search parameters (with URL for turning each
        parameter off)
        """
        parameters = [[k, v] for k, v in self.req.items()
                       if k not in ('page') and v not in ('any')]
        for p in parameters:
            j = {k: v for k, v in self.req.items() if k != p[0]}
            argstring = '&'.join(['%s=%s' % (k, v) for k, v in j.items()])
            p.append(argstring)
        parameters.sort(key=lambda p: p[0])
        return parameters

    def sample_controls(self):
        """
        Controls for generating a sample set from the current
        search parameters.
        """
        parameters = [[k, v] for k, v in self.req.items()
                      if k not in ('page', 'sample') and
                      v not in ('any')]
        argstring = '&'.join(['%s=%s' % (k, v) for k, v in parameters])
        samplers = []
        for size in (10, 50, 100, 200):
            samplers.append((size, argstring + '&sample=%d' % size))
        return samplers

    def list_results(self):
        page_num = int(self.req.get('page', 1))
        qset = self._build_queryset()

        # Keep track of number of results *before* any sampling
        results_count = qset.count()

        if self.req.get('sample') is not None:
            # Random sample from this results set
            qset = self._sample_slice(qset, self.req.get('sample'))
            results = sorted(list(qset), key=lambda r: r.lemmasort)
            paginators = (None, None) # samples aren't paginated

        else:
            # slice into a single page of results
            paged = Paginator(qset, results_per_page)

            try:
                results = paged.page(page_num)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                results = paged.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999),
                #  deliver the last page of results.
                results = paged.page(paged.num_pages)
            paginators = self._paginators(results)

        return results, paginators, results_count

    def analyse_result_set(self, **kwargs):
        if kwargs.get('snapshot'):
            features = (('status', 'status'), ('reasoncode', 'reason code'))
        else:
            features = (('status', 'status'),
                        ('wordclass', 'wordclass'),
                        ('subentrytype', 'sense type'),
                        ('undefined', 'definition status'),
                        ('reasoncode', 'reason code'),
                        ('level2branch', 'branch'),
                        ('user', 'last edited by'),)
        qset = self._build_queryset()
        counts = {}
        for feature, display in features:
            fcounts = qset.values(feature).annotate(count=Count(feature)).order_by()
            counts[display] = [DataPoint(self.req, feature, display,
                               s[feature], s['count']) for s in fcounts
                               if s[feature] is not None]
        for val in counts.values():
            val.sort(key=lambda a: a.count, reverse=True)

        # Drop wordclass-level branches
        if 'branch' in counts:
            counts['branch'] = [v for v in counts['branch'] if not '[' in
                                v.value_display()]

        countlist = []
        for feature, display in features:
            if display in counts and counts[display]:
                countlist.append((display, counts[display]))

        classified_total = 0
        if 'status' in counts:
            for c in counts['status']:
                if c.value in classified_statuses_set:
                    classified_total += c.count

        return countlist, qset.count(), classified_total

    def _build_queryset(self):
        lemma = self.req.get('lemma', 'a_zzz')
        headword = self.req.get('headword')
        wordclass = self.req.get('wordclass')
        sensetype = self.req.get('sensetype')
        defstatus = self.req.get('defstatus')
        reasoncode = self.req.get('reasoncode')
        branch = self.req.get('branch')
        bayesmismatch = self.req.get('bayesmismatch')
        splitdefinition = self.req.get('splitdefinition')
        marking = self.req.get('marking')
        includetopical = bool(self.req.get('includetopicalclassifications'))
        username = self.req.get('editedby')
        delta = int(self.req.get('delta', 0))

        # first cut of qset (based on alphabetical lemma range)
        lemma_from, lemma_to = lemma_splitter(lemma)
        qset = Sense.objects.filter(lemmasort__gte=lemma_from,
                                    lemmasort__lte=lemma_to,)

        # Entry headword
        if headword is not None and headword:
            hw_from, hw_to = lemma_splitter(headword)
            qset = qset.filter(headwordsort__gte=hw_from,
                               headwordsort__lte=hw_to)

        # Wordclass
        if wordclass is not None and wordclass not in ('any', 'all'):
            qset = qset.filter(wordclass=wordclass.upper())

        # Sense type (main sense, compound, etc.)
        if sensetype is not None and sensetype not in ('any', 'all'):
            qset = qset.filter(subentrytype=sensetype)

        # Defined or undefined?
        if defstatus == 'defined':
            qset = qset.filter(undefined=False)
        elif defstatus == 'undefined':
            qset = qset.filter(undefined=True)

        # Thesaurus branch of classification (if any)
        if branch is not None and branch not in ('any', 'all'):
            qset = qset.filter(level2branch=int(branch))

        # Reason-code for classification
        if reasoncode is not None and reasoncode not in ('any', 'all'):
            qset = qset.filter(reasoncode=reasoncode)

        # User
        if username is not None and username not in ('any', 'all'):
            qset = qset.filter(user__username=username)

        # Filter by date/time (timestamp)
        if delta:
            cutoff = datetime.now() - timedelta(minutes=delta)
            qset = qset.filter(timestamp__gte=cutoff)

        # Is the thesaurus class mismatched with the Bayes classification?
        if bayesmismatch == 'yes':
            qset = qset.filter(bayesmismatch=True)
        elif bayesmismatch == 'no':
            qset = qset.filter(bayesmismatch=False)

        # Is the definition split?
        if splitdefinition == 'yes':
            qset = qset.filter(splitdefinition=True)
        elif splitdefinition == 'no':
            qset = qset.filter(splitdefinition=False)

        # Should topical (topc) classifications be included?
        if not includetopical:
            qset = qset.exclude(reasoncode='topc')

        # Status (classified/unclassified/intractable)
        passed_statuses = [s for s in ('classified', 'unclassified',
                           'intractable') if self.req.get(s)]
        # If the search form specifies a reason code, a branch, or a manual
        #  marking, then we force results to be classified senses only,
        #  regardless of any status that's been passed in from the form.
        if ((reasoncode is not None and reasoncode not in ('any', 'all')) or
                (branch is not None and branch not in ('any', 'all')) or
                (marking is not None and marking not in ('any', 'all'))):
            statuses = classified_statuses[:]
        elif passed_statuses:
            statuses = []
            if 'classified' in passed_statuses:
                statuses.extend(classified_statuses[:])
            if 'unclassified' in passed_statuses:
                statuses.append('0')
            if 'intractable' in passed_statuses:
                statuses.append('n')
        else:
            statuses = classified_statuses[:]
        qset = qset.filter(status__in=statuses)

        # Manual marking
        if marking in ('c', 'p', 'i'):
            qset = qset.filter(status=marking)
        elif marking == 'n':
            qset = qset.filter(status__in=['1', 'u', ])

        return qset

    def _paginators(self, results):
        """
        Generate previous/next links
        """
        prevlink = None
        nextlink = None
        if results.has_other_pages():
            current_page = self.path
            args = {k: v for k, v in self.req.items()}
            if results.has_previous():
                args['page'] = str(results.previous_page_number())
                prevlink = current_page + '?' + '&'.join('%s=%s' % (k, v,)
                    for k, v in args.items())
            if results.has_next():
                args['page'] = str(results.next_page_number())
                nextlink = current_page + '?' + '&'.join('%s=%s' % (k, v,)
                    for k, v in args.items())
        return (prevlink, nextlink)

    def _sample_slice(self, qset, sample):
        """
        Random sample from the results set
        """
        samplesize = int(sample)
        # - sort pseudo-randomly (using the sampleorder attribute);
        qset = qset.order_by('sampleorder')
        # - extract a slice of the right size from a random starting point.
        possible_startpoints = qset.count() - samplesize
        if possible_startpoints < 0:
            startpoint = 0
        else:
            startpoint = random.randint(0, possible_startpoints)
        qset = qset[startpoint:startpoint+samplesize]
        return qset


class DataPoint(object):
    wordclass_map = {'NN': 'noun', 'JJ': 'adjective', 'VB': 'verb',
                     'RB': 'adverb', 'PHRASE': 'phrase', 'UH': 'interjection',}
    defstatus_map = {True: 'undefined', False: 'defined'}
    status_map = {'1': 'classified (unmarked)', '0': 'unclassified',
                  'n': 'intractable', 'c': 'marked as correct',
                  'p': 'marked as partially correct',
                  'i': 'marked as incorrect',}

    def __init__(self, request, feature, feature_display, value, count):
        self.feature = feature
        self.feature_display = feature_display
        self.value = value
        self.count = count
        self.filter_added = self.add_filter(request)

    def value_display(self):
        if self.feature_display == 'branch':
            thesclass = ThesaurusClass.objects.get(id=int(self.value))
            return thesclass.breadcrumb
        elif self.feature_display == 'wordclass':
            try:
                return self.wordclass_map[self.value]
            except KeyError:
                return self.value
        elif self.feature_display == 'definition status':
            try:
                return self.defstatus_map[self.value]
            except KeyError:
                return self.value
        elif self.feature_display == 'status':
            try:
                return self.status_map[self.value]
            except KeyError:
                return self.value
        elif self.feature_display == 'reason code':
            return code_interpreter(self.value)
        elif self.feature_display == 'last edited by':
            user = User.objects.get(id=int(self.value))
            return user.username
        else:
            return self.value

    def add_filter(self, request):
        j = {k: v for k, v in request.items() if k not in ('page')}

        if self.feature_display == 'status':
            for status in ('classified', 'unclassified', 'intractable'):
                try:
                    del(j[status])
                except KeyError:
                    pass
                if self.value == status[0]:
                    j[status] = 'on'
        else:
            keyname = self.feature
            value = self.value
            if self.feature_display == 'branch':
                keyname = 'branch'
            elif self.feature_display == 'sense type':
                keyname = 'sensetype'
            elif self.feature_display == 'last edited by':
                keyname = 'editedby'
                value = self.value_display()
            elif self.feature_display == 'definition status':
                keyname = 'defstatus'
                if self.value == True:
                    value = 'undefined'
                else:
                    value = 'defined'
            j[keyname] = value

        return '&'.join(['%s=%s' % (k, v) for k, v in j.items()])


def lemma_splitter(lemstring):
    if lemstring is None or not lemstring:
        return (None, None)
    else:
        if len(lemstring.split('_', 1)) == 2:
            lemma_from, lemma_to = lemstring.split('_', 1)
        elif lemstring.endswith('*'):
            lemma_from = lemstring.replace('*', '')
            lemma_to = lemstring.replace('*', '') + 'zz'
        else:
            lemma_from = lemma_to = lemstring

        return (re.sub(r'[* _]', '', lemma_from),
            re.sub(r'[* _]', '', lemma_to))
