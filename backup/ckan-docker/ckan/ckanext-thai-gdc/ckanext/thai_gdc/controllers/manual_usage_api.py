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

class ManualUsageApiController(p.toolkit.BaseController):

    def manual_usage_api(self, data=None, errors=None, error_summary=None):
        try:
            data = thai_gdc_h.get_ckanext_pages_list_page("2")
        except Exception as e:
            errors = e.error_dict
            error_summary = e.error_summary
        log.info(data)
        data = data[0] or {}
        extra_vars = {}
        errors = errors or {}
        error_summary = error_summary or {}
        extra_vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        return p.toolkit.render('manual_usage_api/manual_usage_api_page.html',extra_vars=extra_vars)
