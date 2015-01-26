from functools import update_wrapper

from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.http import HttpResponsePermanentRedirect, QueryDict
from django.shortcuts import resolve_url
from django.utils.six.moves.urllib.parse import urlparse, urlunparse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect


def AdminExternalAuthMixin(object):
    """Mixin for ``AdminSite`` to use project-level authentication views.

    The admin site's ``login`` and ``logout`` views are replaced with redirects
    to ``LOGIN_URL`` and ``LOGOUT_URL`` (as defined in the settings file). If
    an anonymous user tries to access the admin site, they get redirected to
    ``LOGIN_URL``. If an authenticated user who isn't a staff member tries it,
    they get ``PermissionDenied``.
    """

    def admin_view(self, view, cacheable=False):
        """
        Decorator to create an admin view attached to this ``AdminSite``. This
        wraps the view and provides permission checking by calling
        ``self.has_permission``.

        Unlike the original ``admin_view`` wrapper which this overrides, this
        wrapper raises ``PermissionDenied`` if an authenticated user fails the
        permission check, rather than asking them to log in again. Anonymous
        users are redirected to the project-level login page.

        The caching prevention and CSRF protection features of the wrapper are
        duplicated from the original.
        """
        if view == self.logout:
            # The logout view is wrapped in AdminSite's implementation of
            # get_urls, but this is no longer necessary since it's just a
            # redirect.  Rather than override get_urls, we explicitly exempt
            # it here.  (login isn't wrapped, so it doesn't need an exemption.)
            return view
        def inner(request, *args, **kwargs):
            if not request.user.is_authenticated():
                # Inner import to prevent django.contrib.admin (app) from
                # importing django.contrib.auth.models.User (unrelated model).
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            elif not self.has_permission(request):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        if not cacheable:
            inner = never_cache(inner)
        # We add csrf_protect here so this function can be used as a utility
        # function for any view, without having to repeat 'csrf_protect'.
        if not getattr(view, 'csrf_exempt', False):
            inner = csrf_protect(inner)
        return update_wrapper(inner, view)

    def logout(self, request, extra_context=None):
        """Redirect to the project-level logout page."""
        return HttpResponsePermanentRedirect(resolve_url(settings.LOGOUT_URL))

    def login(self, request, extra_context=None):
        """Redirect to the project-level login page."""
        resolved_url = resolve_url(settings.LOGIN_URL)
        login_url_parts = list(urlparse(resolved_url))
        if REDIRECT_FIELD_NAME in request.GET:
            querystring = QueryDict(login_url_parts[4], mutable=True)
            querystring[REDIRECT_FIELD_NAME] = request.GET[REDIRECT_FIELD_NAME]
            login_url_parts[4] = querystring.urlencode(safe='/')
        return HttpResponsePermanentRedirect(urlunparse(login_url_parts))


class AdminSiteWithExternalAuth(AdminExternalAuthMixin, AdminSite):
    """A Django ``AdminSite`` that uses project-level authentication views."""
