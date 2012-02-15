# Ldap authentication backend for Django. Users are authenticated against
# an ldap server and their django accounts (name, email) are maintained
# automatically.
#
# Configuration is done in settings.py, these are the available settings:
#
# # Where to find the ldap server (optional, default: ldap://localhost)
# AUTH_LDAP_HOST = 'ldap://ldap.kaarsemaker.net'
# # Which ldap groups to mirror in django (optional, default [])
# AUTH_LDAP_GROUPS = ('webadmins','ubuntu')
# # The users must be in any of these groups (optional, default [])
# AUTH_LDAP_FILTER_GROUPS = AUTH_LDAP_GROUPS
# # DN for binding to the server (optional, default anonymous bind)
# #AUTH_LDAP_BINDDN = "cn=admin,dc=kaarsemaker,dc=net"
# #AUTH_LDAP_BINDPW = "TheAdminPassword
# # Base DN for users and groups (required)
# AUTH_LDAP_BASEDN_USER = 'ou=People,dc=kaarsemaker,dc=net'
# AUTH_LDAP_BASEDN_GROUP = 'ou=Group,dc=kaarsemaker,dc=net'
# # Do we need to make the user staff?
# AUTH_LDAP_CREATE_STAFF = True
#
# # If you want LDAP to be your only authentication source, use
# AUTHENTICATION_BACKENDS = ('myproject.auth_ldap.LdapAuthBackend',)
# # If you want to use ldap and fall back to django, use
# AUTHENTICATION_BACKENDS = ('myproject.auth_ldap.LdapAuthBackend',
#							'django.contrib.auth.backends.ModelBackend')
#
# When using ldap exclusively, the superuser created with ./manage.py 
# cannot log in unless the account also exists in ldap. So either make
# sure the user exists in ldap or give another user superuser rights
# before disabling the builtin authentication.
#
# Make sure all your ldap users have a mail attribute, otherwise this
# module will break.
#
# If you use django with mod_python, please make sure no other apache module
# drags in a different version of libldap than what python wants to link to
# or you will see protocol errors. If a ./manage.py runserver instance works
# but apache not, try switching to mod_fcgi, which runs the django code in a
# separate process.
#
# Copyright (c) 2008,2009 Dennis Kaarsemaker <dennis@kaarsemaker.net>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
#	 1. Redistributions of source code must retain the above copyright notice, 
#		this list of conditions and the following disclaimer.
#	 
#	 2. Redistributions in binary form must reproduce the above copyright 
#		notice, this list of conditions and the following disclaimer in the
#		documentation and/or other materials provided with the distribution.
# 
#	 3. Neither the name of Django nor the names of its contributors may be used
#		to endorse or promote products derived from this software without
#		specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from django.contrib.auth.models import User, Group
from django.contrib.auth.backends import ModelBackend
from django.conf import settings
import ldap

from timeline.permissions import set_permission

ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

def _find_dn(ls, username):
	ls.bind_s(getattr(settings, 'AUTH_LDAP_BINDDN', ''),
			  getattr(settings, 'AUTH_LDAP_BINDPW', ''))
	res = ls.search_s(settings.AUTH_LDAP_BASEDN_USER, ldap.SCOPE_ONELEVEL,
					  "uid=" + username, [])
	if not len(res):
		return
	return res[0]

def _find_groups(ls, username):
	if not getattr(settings, 'AUTH_LDAP_GROUPS', None) and \
	   not getattr(settings, 'AUTH_LDAP_FILTER_GROUPS', None):
		return []
	ls.bind_s(getattr(settings, 'AUTH_LDAP_BINDDN', ''),
			  getattr(settings, 'AUTH_LDAP_BINDPW', ''))
	res = ls.search_s(settings.AUTH_LDAP_BASEDN_GROUP, ldap.SCOPE_ONELEVEL,
					  "memberUid=" + username, [])
	return [x[1]['cn'][0] for x in res]

class LdapAuthBackend(ModelBackend):
	def authenticate(self, username=None, password=None):
		# Authenticate against ldap
		ls = ldap.initialize(getattr(settings, 'AUTH_LDAP_HOST', 'ldap://localhost'))
		dn, attrs = _find_dn(ls, username)
		if not dn:
			ls.unbind()
			return
		try:
			ls.bind_s(dn, password)
		except ldap.INVALID_CREDENTIALS:
			ls.unbind()
			return

		# Are we allowed to log in
		groups = _find_groups(ls, username)
		if getattr(settings, 'AUTH_LDAP_FILTER_GROUPS', None):
			for group in getattr(settings,'AUTH_LDAP_FILTER_GROUPS',[]):
				if group in groups:
					break
			else:
				ls.unbind()
				return

		# OK, we've authenticated. Do we exist?
		try:
			user = User.objects.get(username=username)
		except User.DoesNotExist:
			user = User.objects.create_user(username, attrs['mail'][0], password)
			# Save a basic user profile
			user.is_active = True
			if getattr(settings, 'AUTH_LDAP_CREATE_STAFF', False):
				user.is_staff = True
			
			'''
			Call the set_permission function to set the appropriate set of permissions
			User will be able to login to the admin area
			User can add, change, delete timelines and events
			'''
			# user_permissions = set_permission(user)
			user.has_perm('cndlstimeline.add_event')

		user.first_name = attrs['givenname'][0]
		user.last_name = attrs['sn'][0]
		try:
			user.email = attrs['mail'][0]
		except KeyError:
			user.email = username + '@georgetown.edu'
		user.password = 'This is an LDAP account'
		
		# Extra fields - affiliations, primary affiliation, primary department
		# Set the primary department based on the LDAP department code
		#primary_dept_code = Department.objects.get(code=int(attrs['departmentnumber'][0]))
		#user.primary_department = primary_dept_code.id

#		for affiliation in attrs['guaffiliations']:
#			if affiliation == 'Student':
#				user.student = True
#			if affiliation == 'Employee':
#				user.employee = True
#			if affiliation == 'Faculty':
#				user.faculty = True
#			if affiliation == 'Alumni':
#				user.alumni = True
#		for key, value in AFFILIATION_TYPES:
#			if attrs['guprimaryaffiliation'][0] == value:
#				user.primary_affiliation = key
		
		# Group manglement
		for group in getattr(settings,'AUTH_LDAP_GROUPS',[]):
			dgroup, created = Group.objects.get_or_create(name=group)
			if created:
				dgroup.save()
			if dgroup in user.groups.all() and group not in groups:
				user.groups.remove(dgroup)
			if dgroup not in user.groups.all() and group in groups:
				user.groups.add(dgroup)

		# Done!
		user.save()

		ls.unbind()
		return user
