import ckan.plugins as p
import ckan.lib.helpers as h
from ckan.plugins.toolkit import _
import ckan.lib.uploader as uploader
from ckanext.thai_gdc import helpers as thai_gdc_h

from ckan.plugins.toolkit import (
    _, h, request,
    )

class ManualUsageApiController(p.toolkit.BaseController):

    def manual_usage_api(self):
        return p.toolkit.render('manual_usage_api/manual_usage_api_page.html')
