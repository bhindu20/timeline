from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^(?P<user_id>\d+)/(?P<timeline_id>\d+)/$', 'cndlstimeline.views.display'),
    url(r'^get-timeline/$', 'cndlstimeline.views.get_timeline')
)