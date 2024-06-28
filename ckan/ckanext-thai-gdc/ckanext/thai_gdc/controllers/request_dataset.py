# -*- coding: utf-8 -*-
import ckan.plugins as p
import ckan.lib.helpers as helpers
import ckan.lib.captcha as captcha
import logging
from ckan.common import request
from ckanext.thai_gdc import helpers as thai_gdc_h

log = logging.getLogger(__name__)

from ckan.plugins.toolkit import (_)

class RequestDatasetController(p.toolkit.BaseController):

    def index(self, data=None, errors=None, error_summary=None):
        submit_success = False  # Initialize submit_success flag
        
        if request.params:
                request.form = request.params
        if p.toolkit.request.method == 'POST' and not data:
                data = dict(p.toolkit.request.POST)
                try:
                    captcha.check_recaptcha(request)
                except captcha.CaptchaError:
                    error_msg = _(u'Bad Captcha. Please try again.')
                    helpers.flash_error(error_msg)
                    form_vars = {
                        u'data': data or {},
                        u'errors': errors or {},
                        u'error_summary': error_summary or {}
                    }

                    extra_vars = {
                        u'form': p.toolkit.render('requestdataset/snippets/requestdataset_form.html', form_vars)
                    }
                    return p.toolkit.render('requestdataset/requestdataset_page.html', extra_vars=extra_vars)
                
                data_dict_event = {
                     'fields' : {
                        'first_name': data['first_name'],
                        'last_name': data['last_name'],
                        'email': data['email'],
                        'owner_org': data['owner_org'],
                        'package_name': data['package_name'],
                        'notes': data['notes'],
                        'scope': data['scope'],
                        'objective': data['objective'],
                        'modified': data['modified'],
                    }
                }
                try:
                    p.toolkit.get_action('validate_request_dataset')(data_dict=data_dict_event)
                except p.toolkit.ValidationError as e:
                    errors = e.error_dict
                    error_summary = e.error_summary
                    form_vars = {
                        u'data': data or {},
                        u'errors': errors,
                        u'error_summary': error_summary
                    }

                    extra_vars = {
                        u'form': p.toolkit.render('requestdataset/snippets/requestdataset_form.html', form_vars)
                    }
                    return p.toolkit.render('requestdataset/requestdataset_page.html', extra_vars=extra_vars)
                
                # Attempt to add package request
                try:
                    thai_gdc_h.add_package_request(data)
                    submit_success = True
                    form_vars = {
                        u'data': {},
                        u'errors': errors or {},
                        u'error_summary': error_summary or {}
                    }

                    extra_vars = {
                        u'form': p.toolkit.render('requestdataset/snippets/requestdataset_form.html', form_vars)
                    }

                    rendered_template = p.toolkit.render('requestdataset/requestdataset_page.html', extra_vars=extra_vars)

                    if submit_success:
                        modal_script = "<script>$('#requestdataset_success').modal('show');</script>"
                        rendered_template += modal_script
                    return rendered_template
                except p.toolkit.ValidationError as e:
                    errors = e.error_dict
                    error_summary = e.error_summary
                    form_vars = {
                        u'data': data or {},
                        u'errors': errors,
                        u'error_summary': error_summary
                    }

                    extra_vars = {
                        u'form': p.toolkit.render('requestdataset/snippets/requestdataset_form.html', form_vars)
                    }
                # Check if the request was successful and set a flag accordingly
                    return p.toolkit.render('requestdataset/requestdataset_page.html', extra_vars=extra_vars)
        data = data or {}
        error_summary = error_summary or {}
        errors = errors or {}
        form_vars = {
            u'data': data or {},
            u'errors': errors,
            u'error_summary': error_summary
        }

        extra_vars = {
            u'form': p.toolkit.render('requestdataset/snippets/requestdataset_form.html', form_vars)
        }
        return p.toolkit.render('requestdataset/requestdataset_page.html', extra_vars=extra_vars)
