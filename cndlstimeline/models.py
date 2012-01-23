from django.db import models
from django.contrib.auth.models import User
from timeline.settings import UPLOAD_PATH

# "id":"jshist",
# "title":"A little history of JavaScript",
# "description":"Mainly, showing the emergence of different JS libraries.",
# "focus_date":"1996-07-01 12:00:00",
# "timezone":"-07:00",
# "initial_zoom":"37",
# "events":[

# {
# "id":"jshist-self",
# "title": "Sedfslf",
# "description":"Self, one of the inspirations for Javascript's simplicity, is created at Xerox PARC ",
# "startdate": "1986-01-01 12:00:00",
# "importance":"40",
# "date_display":"none",
# "icon":"{{ MEDIA_URL }}css/icons/flag_green.png"
# },


class Event(models.Model):
	title = models.CharField(max_length=255, blank=False)
	description = models.TextField(blank=True)
	startdate = models.DateTimeField()
	importance = models.CharField(max_length=3, default='40',help_text='Choose number from 0 - 100; Higher value ==> more important')
	date_display = models.CharField(max_length=10, default='none')
	link = models.CharField(max_length=255, blank=False)
	icon = models.FileField(upload_to=UPLOAD_PATH+'timelineicons/', blank=True)
	video = models.CharField(max_length=200, blank=True, null=True)
	def __unicode__(self):
		return self.title


# Create your models here.
class CndlsTimeline(models.Model):
	title = models.CharField(max_length=255, blank=False)
	description = models.TextField(blank=True)
	focus_date = models.DateTimeField()
	timezone = models.CharField(max_length=255, blank=True)
	initial_zoom = models.PositiveIntegerField(default=37)
	events = models.ManyToManyField(Event, blank=True, null=True)
	owner = models.ForeignKey(User, null=True, blank=True)

	def __unicode__(self):
		return self.title