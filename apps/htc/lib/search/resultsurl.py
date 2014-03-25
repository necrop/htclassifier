import re


def results_url(url, args, page_num):
    lemma = sanitize(args.get('lemma', ''))
    if not lemma:
        lemma = 'a_zzz'
    args['lemma'] = lemma

    headword = sanitize(args.get('headword', ''))
    try:
        del(args['headword'])
    except KeyError:
        pass
    if headword:
        args['headword'] = headword

    params = ['%s=%s' % (k, str(v)) for k, v in args.items()
              if not k.startswith('csrf') and k != 'mode' and
              v not in ('', 'any', 'all', 'null')]
    if page_num is not None and page_num > 1:
        params.append('page=%d' % (page_num,))
    return '%s?%s' % (url, '&'.join(params),)


def sanitize(lemma):
    l = re.sub(r'[^a-z*_]', '', lemma.lower())
    return l.strip('_')


def update_session(request, args):
    if args.get('mode') == 'quick':
        request.session['htc_quick'] = args.get('lemma') or args.get('headword')
    elif args.get('mode') == 'advanced':
        request.session['htc_advanced'] = {k: v for k, v in
                                           args.items() if
                                           not k.startswith('csrf')
                                           and k != 'mode'}
