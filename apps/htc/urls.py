from django.conf.urls import patterns, url

urlpatterns = patterns('apps.htc.views',
    url(r'^/?$', 'homepage', name='home'),
    url(r'^home$', 'homepage', name='home'),
    url(r'^info/(?P<page>[a-z]+)$', 'info', name='info'),

    url(r'^sense/(?P<id>\d+)$', 'sense_display', name='sense'),

    url(r'^search$', 'search_form', name='searchform'),
    url(r'^submitsearch$', 'search_submit', name='submitsearch'),
    url(r'^searchresults$', 'search_results', name='searchresults'),
    url(r'^analyse$', 'analyse_results', name='analyseresults'),
    url(r'^snapshot$', 'snapshot', name='snapshot'),
    url(r'^toggleeditmode$', 'toggle_edit_mode', name='toggleeditmode'),
    url(r'^updateCheckbox$', 'update_checkbox', name='updatecheckbox'),
    url(r'^addcomment$', 'add_comment', name='addcomment'),
    url(r'^deletecomment/(?P<id>\d+)$', 'delete_comment', name='deletecomment'),
    url(r'^redirectlink$', 'redirect_link', name='redirectlink'),
    url(r'^shiftlink/(?P<senseid>\d+)/(?P<count>\d+)/(?P<classid>\d+)/$', 'shift_link', name='shiftlink'),
    url(r'^localtree/(?P<senseid>\d+)/(?P<count>\d+)/(?P<currentid>\d+)/(?P<centralid>\d+)/$', 'compose_local_tree', name='localtree'),
    url(r'^sensedetailsjson/(?P<senseid>\d+)$', 'sense_details_json', name='sensedetailsjson'),
    url(r'^userdetails$', 'user_details', name='userdetails'),
    url(r'^userdetails/(?P<status>[a-z]+)$', 'user_details', name='userdetailsstatus'),
    url(r'^changeuserdetails$', 'change_user_details', name='changeuserdetails'),
)
