# django-admin-external-auth

Use your Django project's existing authentication views in the admin interface.

## Dependencies

Requires Django 1.7 or later.

## Installation

Download from the Python Package Index with `pip install django-admin-external-auth`. Or download the source from GitHub and install with `python setup.py install`.

## Configuration

In your Django project's settings file, under `INSTALLED_APPS`, find `'django.contrib.admin'` and replace it with `'django.contrib.admin.apps.SimpleAdminConfig'`.

In your Django project's root URLconf, add the following lines somewhere before the first reference to `admin.site`:

    from daeauth import AdminSiteWithExternalAuth
    admin.site = AdminSiteWithExternalAuth()
    admin.autodiscover()

And that's it.
