from timeline.cndlstimeline.models import *

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.core import serializers
from django.forms.models import model_to_dict
from django.utils import simplejson
from django.db.models.query import QuerySet
from django.core.serializers.json import DjangoJSONEncoder
from timeline.settings import UPLOAD_PATH, MEDIA_URL

class HandleQuerySets(DjangoJSONEncoder):
     """ DjangoJSONEncoder extension: handle querysets """
     def default(self, obj):
         if isinstance(obj, QuerySet):
             return serializers.serialize("python", obj, ensure_ascii=False)
         return DjangoJSONEncoder.default(self, obj)

def display(request, user_id, timeline_id):
	owner = User.objects.get(id=user_id)
	timeline = CndlsTimeline.objects.get(id=timeline_id)
	events = timeline.events.all()
	
	events = []

	for event in timeline.events.all():
		event_dict = {}
		event_dict['id'] = str(timeline.title)+'-'+str(event.id)
		event_dict['title'] = event.title
		event_dict['description'] = event.description
		event_dict['startdate'] = event.startdate
		event_dict['importance'] = event.importance
		# event_dict['icon'] = 'circle_green.png'
		if event.icon:
			path = str(event.icon)
			folder_filename = path.replace(UPLOAD_PATH,'')
			icon_url = MEDIA_URL+folder_filename
			event_dict['icon'] = folder_filename
		else:
			event_dict['icon'] = 'timelineicons/circle_green.png'
		event_dict['link'] = event.link
		event_dict['video'] = event.video
		event_dict['date_display'] = event.date_display
		events.append(event_dict)

	
	new_time = {}
	new_time['id'] = timeline.title
	new_time['title'] = timeline.title
	new_time['description'] = timeline.description
	new_time['initial_zoom'] = timeline.initial_zoom
	new_time['focus_date'] = timeline.focus_date
	new_time['events'] = events
	new_time['timezone'] = timeline.timezone

	# new_time = model_to_dict(timeline)
	#timeline = simplejson.dumps( new_time, cls=HandleQuerySets )

	
	import json
	timeline = json.dumps([new_time], cls=HandleQuerySets)


	return render_to_response('cndlstimeline/display-timeline.html',
                    { 'timeline': timeline,
                      'events': events
                    },
                    context_instance=RequestContext(request))
	
