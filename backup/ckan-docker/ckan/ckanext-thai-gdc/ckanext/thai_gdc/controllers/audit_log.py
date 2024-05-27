import ckan.plugins as p
import ckan.lib.helpers as helpers
from ckan.plugins.toolkit import _
import ckan.lib.uploader as uploader
from ckanext.thai_gdc import helpers as thai_gdc_h
from ckan.common import config

from ckan.plugins.toolkit import (
    _, h, request,
    )

class AuditLogController(p.toolkit.BaseController):

    def index(self, data=None, errors=None, error_summary=None):
        is_access = helpers.check_access('config_option_update')

        limit = int(config.get(u'ckan.datasets_per_page', 20))
        extra_vars = {}
        extra_vars[u'page'] = helpers.Page(
            collection=[],
            items_per_page=limit
        )
        q = request.params.get(u'q', u'')
        
        
        try:
            extra_vars[u'page'].items = thai_gdc_h.get_audit_log_list(q)
            extra_vars[u'page'].item_count = len(extra_vars[u'page'].items)
        except p.toolkit.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.index(extra_vars[u'page'].items, errors, error_summary)
        
        errors = errors or {}
        error_summary = error_summary or {}
        extra_vars[u'errors'] = errors 
        extra_vars[u'error_summary'] = error_summary
        extra_vars[u'count'] = len(extra_vars[u'page'].items)
        extra_vars[u'q'] = q
        return p.toolkit.render('admin/audit_log.html', extra_vars=extra_vars)
