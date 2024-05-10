# -*- coding: utf-8 -*-
import ckan.plugins as plugins
import ckan.lib.helpers as helpers
import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.model as model
import logging
from ckan.common import g
from pylons import config

from ckan.plugins.toolkit import (
    _, c, h, BaseController, check_access, NotAuthorized, abort, render,
    redirect_to, request,
    )

from ckan.controllers.home import CACHE_PARAMETERS
from ckanext.thai_gdc import helpers as thai_gdc_h

_validate = dict_fns.validate
ValidationError = logic.ValidationError

log = logging.getLogger(__name__)

class UserManageController(plugins.toolkit.BaseController):

    def user_active(self):
        data = request.GET
        if 'id' in data:
            try:
                data_dict = logic.clean_dict(
                    dict_fns.unflatten(
                        logic.tuplize_dict(
                            logic.parse_params(
                                request.GET, ignore_keys=CACHE_PARAMETERS))))
                
                context = {
                    u'model': model,
                    u'session': model.Session,
                    u'user': g.user,
                    u'auth_user_obj': g.userobj,
                    u'for_view': True
                }
                check_access('user_update', context, {})
                user_dict = plugins.toolkit.get_action('user_show')(None, {'id':data['id']})
                if user_dict and user_dict['state'] == 'deleted':
                    user = model.User.get(user_dict['name'])
                    user.state = model.State.ACTIVE
                    user.save()
                h.redirect_to(controller='user', action='read', id=data['id'])
            except logic.ValidationError as e:
                return e
    def articles_news(self):
        return plugins.toolkit.render('articles_news/articles_news_list.html')
    





    
    def requestdataset(self, data=None, errors=None, error_summary=None):
        submit_success = False  # Initialize submit_success flag
        
        if plugins.toolkit.request.method == 'POST' and not data:
                data = dict(plugins.toolkit.request.POST)
                try:
                        # Attempt to add package request
                        data = thai_gdc_h.add_package_request(data)
                        print(data)
                        # Check if the request was successful and set a flag accordingly
                        submit_success = True
                except plugins.toolkit.ValidationError as e:
                        # Handle validation errors
                        errors = e.error_dict
                        error_summary = e.error_summary
                        return self.index(data, errors, error_summary)

        # Initialize errors and error_summary if not provided
        errors = errors or {}
        error_summary = error_summary or {}

        # Pass the data, errors, and error_summary to the template
        extra_vars = {'data': data, 'errors': errors, 'error_summary': error_summary}

        # Render the template, passing extra_vars
        rendered_template = plugins.toolkit.render('requestdataset/requestdataset_page.html', extra_vars=extra_vars)
        
        # If submission was successful, append JavaScript code to display the modal
        if submit_success:
                modal_script = "<script>$('#requestdataset_success').modal('show');</script>"
                rendered_template += modal_script
        # else:
        #         # Do something else if submission was not successful
        #         modal_script = "<script>$('#requestdataset_erroor').modal('show');</script>"
        #         rendered_template += modal_script
        
        return rendered_template
    


    def user_create(self, data=None, errors=None, error_summary=None):
        submit_success = False  # Initialize submit_success flag
        
        if plugins.toolkit.request.method == 'POST' and not data:
                data = dict(plugins.toolkit.request.POST)
                print(data)
                try:
                        # Attempt to add package request
                        data = thai_gdc_h.add_user_create(data)
                        
                        # Check if the request was successful and set a flag accordingly
                        submit_success = True
                except plugins.toolkit.ValidationError as e:
                        # Handle validation errors
                        errors = e.error_dict
                        error_summary = e.error_summary
                        return self.index(data, errors, error_summary)

        # Initialize errors and error_summary if not provided
        errors = errors or {}
        error_summary = error_summary or {}

        # Pass the data, errors, and error_summary to the template
        extra_vars = {'data': data, 'errors': errors, 'error_summary': error_summary}

        # Render the template, passing extra_vars
        rendered_template = plugins.toolkit.render('user_create/user_create_page.html', extra_vars=extra_vars)
        
        # If submission was successful, append JavaScript code to display the modal
        if submit_success:
                modal_script = "<script>$('#user_create_success').modal('show');</script>"
                rendered_template += modal_script
        # else:
        #         # Do something else if submission was not successful
        #         modal_script = "<script>$('#user_create_erroor').modal('show');</script>"
        #         rendered_template += modal_script
        
        return rendered_template
    


    def newdataset(self):
        return plugins.toolkit.render('newdataset/newdataset_page.html')
    def rollback_trash(self, id=None, errors=None, error_summary=None):
        if id is None:
            return h.redirect_to(u'admin.trash')
        try:
            data = thai_gdc_h.rollback_trash_by_id(id, request.params['ent_type'])
        except plugins.toolkit.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.index(data, errors, error_summary)
        errors = errors or {}
        error_summary = error_summary or {}
        # extra_vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        return h.redirect_to(u'admin.trash')