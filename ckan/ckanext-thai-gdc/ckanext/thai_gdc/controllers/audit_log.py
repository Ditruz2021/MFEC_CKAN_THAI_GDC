import ckan.plugins as p
import ckan.lib.helpers as h
from ckan.plugins.toolkit import _
import ckan.lib.uploader as uploader
from ckanext.thai_gdc import helpers as thai_gdc_h

from ckan.plugins.toolkit import (
    _, h, request,
    )

class AuditLogController(p.toolkit.BaseController):

    def index(self, data=None, errors=None, error_summary=None):
        is_access = h.check_access('config_option_update')
        if request.params:
            q = request.params['q']
        else:
            q = ''
        if not is_access:
            p.toolkit.abort(404, _('Page Not Found'))
        try:
            data = thai_gdc_h.get_audit_log_list(q)
        except p.toolkit.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.index(data, errors, error_summary)
        
        errors = errors or {}
        error_summary = error_summary or {}
        extra_vars = {'data': data, 'errors': errors, 'error_summary': error_summary, 'count': len(data), 'q': q}
        return p.toolkit.render('admin/audit_log.html', extra_vars=extra_vars)
