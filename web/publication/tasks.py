from .models import Publication
import re

def get_latest_publication():
	"""return datetime of the latest publication object"""

	last_publication =Publication.objects.all().order_by('-created_on').first().created_on
	return last_publication

def is_blacklisted(request, default=None):
	''' 
	Return the bool value on the basis of current request whether to show the unpublished data or not.

	Example:

		def some_view(request):
			...
			referer_view = get_referer_view(request)
			return HttpResponseRedirect(referer_view, '/accounts/login/')
	'''

	# if the user typed the url directly in the browser's address bar
	referer = request.META.get('HTTP_REFERER')
	if not referer:
		return default

	blacklist_servers = ['trigger-3.s3-website.ap-south-1.amazonaws.com']

	# remove the protocol and split the url at the slashes
	referer = re.sub('^https?:\/\/', '', referer).split('/')
	if referer[0] in blacklist_servers:
		return True
	else:
		return False

	# add the slash at the relative path's view and finished
	# referer = u'/' + u'/'.join(referer[1:])
	# return referer