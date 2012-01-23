from django.contrib import admin
from timeline.cndlstimeline.models import CndlsTimeline, Event

admin.site.register(CndlsTimeline)
admin.site.register(Event)