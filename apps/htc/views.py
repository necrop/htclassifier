from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse


@login_required
def homepage(request):
    """
    Home page
    """
    params = {}
    return render(request, 'htc/home.html', _add_base_params(params, request))


def info(request, **kwargs):
    template_name = 'htc/info/%s.html' % kwargs.get('page')
    params = {}
    return render(request, template_name, _add_base_params(params, request))


@login_required
def search_form(request, **kwargs):
    from .lib.search.form import SearchForm
    store = request.session.get('htc_advanced', {})
    params = {'form': SearchForm(store)}
    return render(request, 'htc/searchform.html',
                  _add_base_params(params, request))


def search_submit(request, **kwargs):
    from django.core.urlresolvers import reverse
    from .lib.search.resultsurl import results_url, update_session
    if request.method == 'POST':
        post = request.POST.copy()
        update_session(request, post)
        new_url = reverse('htc:searchresults', kwargs={})
        return HttpResponseRedirect(results_url(new_url, post, 1))
    else:
        return redirect(homepage)


def search_results(request, **kwargs):
    from .lib.search.resultslist import ResultsList
    results, paginators, num_all_results = ResultsList(request).list_results()
    analyse_url = request.get_full_path().replace('/searchresults', '/analyse')
    parameters = ResultsList(request).parameter_controls()
    samplers = ResultsList(request).sample_controls()

    if request.GET.get('sample'):
        sample = request.GET.get('sample')
    else:
        sample = False

    if sample:
        summary = ''
    elif num_all_results == 0:
        summary = 'No results found'
    elif num_all_results == 1:
        summary = '1 result'
    else:
        summary = '%d - %d of %d results' % (results.start_index(),
                                             results.end_index(),
                                             num_all_results,)

    params = {'results': results, 'paginators': paginators,
              'summary': summary, 'analyse_url': analyse_url,
              'parameters': parameters, 'sample': sample, 'samplers': samplers,
              'num_results': num_all_results}
    return render(request, 'htc/resultslist.html',
                  _add_base_params(params, request))


def analyse_results(request, **kwargs):
    from .lib.search.resultslist import ResultsList
    counts, total, classified_total = ResultsList(request).analyse_result_set()
    results_url = request.get_full_path().replace('/analyse', '/searchresults')
    parameters = ResultsList(request).parameter_controls()

    params = {'counts': counts, 'total': total, 'parameters': parameters,
              'results_url': results_url, 'path': request.path,
              'classified_total': classified_total, 'snapshot': False}
    return render(request, 'htc/analyseresults.html',
                  _add_base_params(params, request))


@login_required
def snapshot(request, **kwargs):
    from .lib.search.resultslist import ResultsList
    counts, total, classified_total = ResultsList(request).analyse_result_set(snapshot=True)
    results_url = request.get_full_path().replace('/analyse', '/searchresults')
    parameters = ResultsList(request).parameter_controls()

    params = {'counts': counts, 'total': total, 'parameters': parameters,
              'results_url': results_url, 'path': request.path,
              'classified_total': classified_total, 'snapshot': True}
    return render(request, 'htc/analyseresults.html',
                  _add_base_params(params, request))


@login_required
def sense_display(request, **kwargs):
    from .models import Sense
    id = kwargs.get('id')
    try:
        sense = Sense.objects.get(id=id)
    except Sense.DoesNotExist:
        raise Http404
    else:
        params = {'sense': sense}
        return render(request, 'htc/sense.html',
                      _add_base_params(params, request))


def toggle_edit_mode(request, **kwargs):
    referrer = request.META.get('HTTP_REFERER', None)
    if request.session.get('htc_editmode', 'off') == 'off':
        request.session['htc_editmode'] = 'on'
    else:
        request.session['htc_editmode'] = 'off'
    if referrer is not None:
        return HttpResponseRedirect(referrer)
    else:
        return redirect(homepage)


def update_checkbox(request, **kwargs):
    from .lib.statusupdater import update_status
    update_status(request)
    return HttpResponse(status=204)


def add_comment(request, **kwargs):
    from .models import Sense
    referrer = request.META.get('HTTP_REFERER', None)
    if request.method == 'POST':
        post = request.POST.copy()
        id = post.get('senseid')
        try:
            sense = Sense.objects.get(id=id)
        except Sense.DoesNotExist:
            pass
        else:
            comment = post.get('commenttext', '').strip()
            if comment:
                sense.comment = comment
            else:
                sense.comment = None
            sense.save_with_user(request)
        return HttpResponseRedirect(referrer)
    else:
        return redirect(homepage)


def delete_comment(request, **kwargs):
    from .models import Sense
    referrer = request.META.get('HTTP_REFERER', None)
    id = kwargs.get('id')
    try:
        sense = Sense.objects.get(id=id)
    except Sense.DoesNotExist:
        pass
    else:
        sense.comment = None
        sense.save_with_user(request)
    return HttpResponseRedirect(referrer)


def redirect_link(request, **kwargs):
    """
    Move the link from a given sense to point to a new thesaurus class.
    (via form)
    """
    from .lib.classmover import move_class, classid_cleaner
    referrer = request.META.get('HTTP_REFERER', None)
    if request.method == 'POST':
        post = request.POST.copy()
        senseid = int(post.get('senseid'))
        count = int(post.get('count'))
        classid = classid_cleaner(post.get('classid'))
        move_class(request, senseid, classid, count)

        fragment = '#row-%d' % senseid
        return HttpResponseRedirect(referrer + fragment)
    else:
        return redirect(homepage)


def shift_link(request, **kwargs):
    """
    Move the link from a given sense to point to a new thesaurus class.
    (via tree navigation)
    """
    from .lib.classmover import move_class
    referrer = request.META.get('HTTP_REFERER', None)
    senseid = int(kwargs.get('senseid'))
    classid = int(kwargs.get('classid'))
    count = int(kwargs.get('count'))
    move_class(request, senseid, classid, count)

    fragment = '#row-%d' % senseid
    return HttpResponseRedirect(referrer + fragment)


def compose_local_tree(request, **kwargs):
    """
    Return a slug of HTML used to populate the local-context tree in
    the modal pop-up when changing a classification
    """
    from .models import ThesaurusClass, Sense
    senseid = int(kwargs.get('senseid'))
    currentid = int(kwargs.get('currentid'))
    centralid = int(kwargs.get('centralid'))
    count = int(kwargs.get('count'))
    t = get_template('htc/tree_components.html')
    try:
        centralclass = ThesaurusClass.objects.get(id=centralid)
    except ThesaurusClass.DoesNotExist:
        response = ''
    else:
        currentclass = ThesaurusClass.objects.get(id=currentid)
        sense = Sense.objects.get(id=senseid)
        response = t.render(Context({'sense': sense,
                                     'centralclass': centralclass,
                                     'currentclass': currentclass,
                                     'count': count}))
    return HttpResponse(response, content_type='text/plain')


def sense_details_json(request, **kwargs):
    """
    Return a JSON object with basic details about a given sense, used
    to populate the modal pop-up when changing a classification
    """
    import json
    from .models import Sense
    senseid = int(kwargs.get('senseid'))
    try:
        sense = Sense.objects.get(id=senseid)
    except Sense.DoesNotExist:
        response = {'lemma': '?', 'definition': 'undefined', 'link': ''}
    else:
        if sense.definition:
            defn = '"' + sense.definition + '"'
        else:
            defn = '[undefined]'
        response = {'lemma': '%s (%s)' % (sense.lemma, sense.wordclass_readable()),
                    'definition': defn, 'link': sense.oed_url(),}
    return HttpResponse(json.dumps(response), content_type='text/plain')


@login_required
def user_details(request, **kwargs):
    """
    Enable the user to change details and password
    """
    try:
        request.user
    except AttributeError:
        return redirect(homepage)
    else:
        params = {'status': kwargs.get('status', None),}
        return render(request, 'htc/user_details.html',
                      _add_base_params(params, request))


def change_user_details(request, **kwargs):
    from .lib.users.updaterecord import update_record
    if request.method == 'POST':
        post = request.POST.copy()
        status = update_record(request, post)
        return HttpResponseRedirect(reverse('htc:userdetailsstatus',
                                            kwargs={'status': status}))
    else:
        return redirect(homepage)


def _add_base_params(params, request):
    params['quicksearchvalue'] = request.session.get('htc_quick', '')
    params['editmode'] = request.session.get('htc_editmode', 'off')
    try:
        user = request.user
    except AttributeError:
        user = None
    params['user'] = user
    return params
