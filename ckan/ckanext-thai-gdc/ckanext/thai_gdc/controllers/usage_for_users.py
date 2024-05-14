import ckan.plugins as p
import ckan.lib.helpers as h
from ckan.plugins.toolkit import _
import ckan.lib.uploader as uploader
from ckanext.thai_gdc import helpers as thai_gdc_h

from ckan.plugins.toolkit import (
    _, h, request,
    )

class ManualUsageController(p.toolkit.BaseController):

    def usage_for_users(self):
        return p.toolkit.render('usage_for_users/usage_for_users_page.html')
