from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^(?P<user_id>\d+)/(?P<timeline_id>\d+)/$', 'cndlstimeline.views.display'),
)