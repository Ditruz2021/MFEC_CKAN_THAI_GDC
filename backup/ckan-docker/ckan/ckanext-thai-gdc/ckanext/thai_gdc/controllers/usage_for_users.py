import ckan.plugins as p
import ckan.lib.helpers as h
from ckan.plugins.toolkit import _
import ckan.lib.uploader as uploader
from ckanext.thai_gdc import helpers as thai_gdc_h
import logging
from ckan.plugins.toolkit import (
    _, h, request,
    )
log = logging.getLogger(__name__)
class ManualUsageController(p.toolkit.BaseController):

    def usage_for_users(self, data=None, errors=None, error_summary=None):
        try:
            data = thai_gdc_h.get_ckanext_pages_list_page("1")
        except Exception as e:
            errors = e.error_dict
            error_summary = e.error_summary
        log.info(data)
        data = data[0] or {}
        extra_vars = {}
        errors = errors or {}
        error_summary = error_summary or {}
        extra_vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        return p.toolkit.render('usage_for_users/usage_for_users_page.html',extra_vars=extra_vars)

