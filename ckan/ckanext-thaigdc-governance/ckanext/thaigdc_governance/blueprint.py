# encoding: utf-8

from flask import Blueprint
import ckan.plugins.toolkit as toolkit
from ckan.common import g, _, config, request, asbool
import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
from functools import partial
from six.moves.urllib.parse import urlencode
import ckan.plugins as plugins
from ckan.lib.search import SearchError, SearchQueryError
import six
import logging
from ckan.views.dataset import drill_down_url, remove_field, _pager_url, _encode_params, _get_search_details, _sort_by
from ckan.lib.render import TemplateNotFound
import ckan.lib.navl.dictization_functions as dict_fns
from ckanapi import LocalCKAN
import datetime
from ckan import authz
import uuid
from collections import OrderedDict
from ckan.plugins.toolkit import (
    _, c
    )
import os

log = logging.getLogger(__name__)
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError

governance = Blueprint('governance', __name__)

def _extra_template_variables(context, data_dict):
    is_sysadmin = authz.is_sysadmin(g.user)
    try:
        user_dict = logic.get_action(u'user_show')(context, data_dict)
    except logic.NotFound:
        base.abort(404, _(u'User not found'))
    except logic.NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))

    is_myself = user_dict[u'name'] == g.user
    about_formatted = h.render_markdown(user_dict[u'about'])
    extra = {
        u'is_sysadmin': is_sysadmin,
        u'user_dict': user_dict,
        u'is_myself': is_myself,
        u'about_formatted': about_formatted
    }
    return extra

def my_package_requested_list():
    package_type = u'requestdata'

    admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')
    
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }

    extra_vars = _extra_template_variables(context,{'id':g.user})

    extra_vars[u'q'] = q = request.args.get(u'q', u'')

    extra_vars['query_error'] = False
    page = h.get_page_number(request.args)

    limit = int(config.get(u'ckan.datasets_per_page', 20))

    params_nopage = [(k, v) for k, v in request.args.items(multi=True)
                     if k != u'page']

    extra_vars[u'drill_down_url'] = drill_down_url
    extra_vars[u'remove_field'] = partial(remove_field, package_type)

    sort_by = request.args.get(u'sort', None)
    params_nosort = [(k, v) for k, v in params_nopage if k != u'sort']

    extra_vars[u'sort_by'] = partial(_sort_by, params_nosort, package_type)

    if not sort_by:
        sort_by_fields = []
    else:
        sort_by_fields = [field.split()[0] for field in sort_by.split(u',')]
    extra_vars[u'sort_by_fields'] = sort_by_fields

    pager_url = partial(_pager_url, params_nopage, package_type)

    search_url_params = urlencode(_encode_params(params_nopage))
    extra_vars[u'search_url_params'] = search_url_params

    details = _get_search_details()
    extra_vars[u'fields'] = details[u'fields']
    extra_vars[u'fields_grouped'] = details[u'fields_grouped']
    search_extras = details[u'search_extras']

    q += u' +dataset_type:{type} +creator_user_id:{sysadmin} +package_owner:{user} +(request_state:requestdata_wait_maintainer_notify OR request_state:requestdata_wait_received OR request_state:requestdata_received)'.format(type=package_type,sysadmin=_extra_template_variables(context,{'id':admin_user})['user_dict']['id'],user=extra_vars['user_dict']['id'])

    data_dict = {
        u'q': q,
        u'rows': limit,
        u'start': (page - 1) * limit,
        u'sort': sort_by,
        u'extras': search_extras,
        u'include_private': asbool(
            config.get(u'ckan.search.default_include_private', True)
        ),
    }
    try:
        query = plugins.toolkit.get_action('package_search')(context, data_dict)

        extra_vars[u'sort_by_selected'] = query[u'sort']

        extra_vars[u'page'] = h.Page(
            collection=query[u'results'],
            page=page,
            url=pager_url,
            item_count=query[u'count'],
            items_per_page=limit
        )
        extra_vars[u'search_facets'] = {}
        extra_vars[u'page'].items = query[u'results']
    except SearchQueryError as se:
        # User's search parameters are invalid, in such a way that is not
        # achievable with the web interface, so return a proper error to
        # discourage spiders which are the main cause of this.
        log.info(u'Dataset search query rejected: %r', se.args)
        base.abort(
            400,
            _(u'Invalid search query: {error_message}')
            .format(error_message=str(se))
        )
    except SearchError as se:
        # May be bad input from the user, but may also be more serious like
        # bad code causing a SOLR syntax error, or a problem connecting to
        # SOLR
        log.error(u'Dataset search error: %r', se.args)
        extra_vars[u'query_error'] = True
        extra_vars[u'search_facets'] = {}
        extra_vars[u'page'] = h.Page(collection=[])

    extra_vars[u'dataset_type'] = package_type

    # TODO: remove
    for key, value in six.iteritems(extra_vars):
        setattr(g, key, value)

    return toolkit.render('user/dashboard_requestdatas.html',
                           extra_vars=extra_vars)

def my_requestdata_list():
    package_type = u'requestdata'

    admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')
    
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }

    extra_vars = _extra_template_variables(context,{'id':g.user})

    extra_vars[u'q'] = q = request.args.get(u'q', u'')

    extra_vars['query_error'] = False
    page = h.get_page_number(request.args)

    limit = int(config.get(u'ckan.datasets_per_page', 20))

    params_nopage = [(k, v) for k, v in request.args.items(multi=True)
                     if k != u'page']

    extra_vars[u'drill_down_url'] = drill_down_url
    extra_vars[u'remove_field'] = partial(remove_field, package_type)

    sort_by = request.args.get(u'sort', None)
    params_nosort = [(k, v) for k, v in params_nopage if k != u'sort']

    extra_vars[u'sort_by'] = partial(_sort_by, params_nosort, package_type)

    if not sort_by:
        sort_by_fields = []
    else:
        sort_by_fields = [field.split()[0] for field in sort_by.split(u',')]
    extra_vars[u'sort_by_fields'] = sort_by_fields

    pager_url = partial(_pager_url, params_nopage, package_type)

    search_url_params = urlencode(_encode_params(params_nopage))
    extra_vars[u'search_url_params'] = search_url_params

    details = _get_search_details()
    extra_vars[u'fields'] = details[u'fields']
    extra_vars[u'fields_grouped'] = details[u'fields_grouped']
    search_extras = details[u'search_extras']

    q += u' +dataset_type:{type} +creator_user_id:{sysadmin} +requester_id:{user}'.format(type=package_type,sysadmin=_extra_template_variables(context,{'id':admin_user})['user_dict']['id'],user=extra_vars['user_dict']['id'])

    data_dict = {
        u'q': q,
        u'rows': limit,
        u'start': (page - 1) * limit,
        u'sort': sort_by,
        u'extras': search_extras,
        u'include_private': asbool(
            config.get(u'ckan.search.default_include_private', True)
        ),
    }
    try:
        query = plugins.toolkit.get_action('package_search')(context, data_dict)

        extra_vars[u'sort_by_selected'] = query[u'sort']

        extra_vars[u'page'] = h.Page(
            collection=query[u'results'],
            page=page,
            url=pager_url,
            item_count=query[u'count'],
            items_per_page=limit
        )
        extra_vars[u'search_facets'] = {}
        extra_vars[u'page'].items = query[u'results']
    except SearchQueryError as se:
        # User's search parameters are invalid, in such a way that is not
        # achievable with the web interface, so return a proper error to
        # discourage spiders which are the main cause of this.
        log.info(u'Dataset search query rejected: %r', se.args)
        base.abort(
            400,
            _(u'Invalid search query: {error_message}')
            .format(error_message=str(se))
        )
    except SearchError as se:
        # May be bad input from the user, but may also be more serious like
        # bad code causing a SOLR syntax error, or a problem connecting to
        # SOLR
        log.error(u'Dataset search error: %r', se.args)
        extra_vars[u'query_error'] = True
        extra_vars[u'search_facets'] = {}
        extra_vars[u'page'] = h.Page(collection=[])

    extra_vars[u'dataset_type'] = package_type

    # TODO: remove
    for key, value in six.iteritems(extra_vars):
        setattr(g, key, value)

    return toolkit.render('user/dashboard_requestdatas.html',
                           extra_vars=extra_vars)

def _requestdata_processing(page_url_type, request_state):
    package_type = u'requestdata'
    extra_vars = {}
    extra_vars['request_state'] = request_state

    try:
        context = dict(model=model, user=g.user, auth_user_obj=g.userobj)
        logic.check_access(u'steward', context)
    except logic.NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))

    extra_vars[u'q'] = q = request.args.get(u'q', u'')

    extra_vars['query_error'] = False
    page = h.get_page_number(request.args)

    limit = int(config.get(u'ckan.datasets_per_page', 20))

    params_nopage = [(k, v) for k, v in request.args.items(multi=True)
                     if k != u'page']

    extra_vars[u'drill_down_url'] = drill_down_url
    extra_vars[u'remove_field'] = partial(remove_field, package_type)

    sort_by = request.args.get(u'sort', None)
    params_nosort = [(k, v) for k, v in params_nopage if k != u'sort']

    extra_vars[u'sort_by'] = partial(_sort_by, params_nosort, package_type)

    if not sort_by:
        sort_by_fields = []
    else:
        sort_by_fields = [field.split()[0] for field in sort_by.split(u',')]
    extra_vars[u'sort_by_fields'] = sort_by_fields

    pager_url = partial(_pager_url, params_nopage, page_url_type)

    search_url_params = urlencode(_encode_params(params_nopage))
    extra_vars[u'search_url_params'] = search_url_params

    details = _get_search_details()
    extra_vars[u'fields'] = details[u'fields']
    extra_vars[u'fields_grouped'] = details[u'fields_grouped']
    search_extras = details[u'search_extras']

    admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')

    # context = {
    #     u'model': model,
    #     u'session': model.Session,
    #     u'user': admin_user,
    #     u'for_view': True,
    #     u'auth_user_obj': model.User.by_name(admin_user)
    # }

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'auth_user_obj': g.userobj
    }

    q += u' +dataset_type:{type} +creator_user_id:{sysadmin} +request_state:{state}'.format(type=package_type, sysadmin=_extra_template_variables(context,{'id':admin_user})['user_dict']['id'], state=request_state)

    facets = OrderedDict()

    # Facet titles
    for plugin in plugins.PluginImplementations(plugins.IFacets):
        facets = plugin.dataset_facets(facets, package_type)

    extra_vars[u'facet_titles'] = facets

    data_dict = {
        u'q': q,
        u'facet.field': list(facets.keys()),
        u'rows': limit,
        u'start': (page - 1) * limit,
        u'sort': sort_by,
        u'extras': search_extras,
        u'include_private': asbool(
            config.get(u'ckan.search.default_include_private', True)
        ),
    }
    try:
        query = plugins.toolkit.get_action('package_search')(context, data_dict)

        extra_vars[u'sort_by_selected'] = query[u'sort']

        extra_vars[u'page'] = h.Page(
            collection=query[u'results'],
            page=page,
            url=pager_url,
            item_count=query[u'count'],
            items_per_page=limit
        )
        extra_vars[u'search_facets'] = query[u'search_facets']
        extra_vars[u'page'].items = query[u'results']
    except SearchQueryError as se:
        # User's search parameters are invalid, in such a way that is not
        # achievable with the web interface, so return a proper error to
        # discourage spiders which are the main cause of this.
        log.info(u'Dataset search query rejected: %r', se.args)
        base.abort(
            400,
            _(u'Invalid search query: {error_message}')
            .format(error_message=str(se))
        )
    except SearchError as se:
        # May be bad input from the user, but may also be more serious like
        # bad code causing a SOLR syntax error, or a problem connecting to
        # SOLR
        log.error(u'Dataset search error: %r', se.args)
        extra_vars[u'query_error'] = True
        extra_vars[u'search_facets'] = {}
        extra_vars[u'page'] = h.Page(collection=[])
    
    # FIXME: try to avoid using global variables
    g.search_facets_limits = {}
    for facet in extra_vars[u'search_facets'].keys():
        try:
            limit = int(
                request.args.get(
                    u'_%s_limit' % facet,
                    int(config.get(u'search.facets.default', 10))
                )
            )
        except ValueError:
            base.abort(
                400,
                _(u'Parameter u"{parameter_name}" is not '
                  u'an integer').format(parameter_name=u'_%s_limit' % facet)
            )

        g.search_facets_limits[facet] = limit

    extra_vars[u'dataset_type'] = package_type

    # TODO: remove
    for key, value in six.iteritems(extra_vars):
        setattr(g, key, value)

    return extra_vars

def requestdata_processing_wait_steward(request_state = u'requestdata_wait_steward'):
    extra_vars = _requestdata_processing('processing_state_wait_steward', request_state)

    return toolkit.render('requestdata/processing.html',
                           extra_vars=extra_vars)

def requestdata_processing_wait_council(request_state = u'requestdata_wait_council'):
    extra_vars = _requestdata_processing('processing_state_wait_council', request_state)

    return toolkit.render('requestdata/processing.html',
                           extra_vars=extra_vars)

def _requestdata_receive(page_url_type, request_state):
    package_type = u'requestdata'
    extra_vars = {}
    extra_vars['request_state'] = request_state

    try:
        context = dict(model=model, user=g.user, auth_user_obj=g.userobj)
        logic.check_access(u'steward', context)
    except logic.NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))

    extra_vars[u'q'] = q = request.args.get(u'q', u'')

    extra_vars['query_error'] = False
    page = h.get_page_number(request.args)

    limit = int(config.get(u'ckan.datasets_per_page', 20))

    params_nopage = [(k, v) for k, v in request.args.items(multi=True)
                     if k != u'page']

    extra_vars[u'drill_down_url'] = drill_down_url
    extra_vars[u'remove_field'] = partial(remove_field, package_type)

    sort_by = request.args.get(u'sort', None)
    params_nosort = [(k, v) for k, v in params_nopage if k != u'sort']

    extra_vars[u'sort_by'] = partial(_sort_by, params_nosort, package_type)

    if not sort_by:
        sort_by_fields = []
    else:
        sort_by_fields = [field.split()[0] for field in sort_by.split(u',')]
    extra_vars[u'sort_by_fields'] = sort_by_fields

    pager_url = partial(_pager_url, params_nopage, page_url_type)

    search_url_params = urlencode(_encode_params(params_nopage))
    extra_vars[u'search_url_params'] = search_url_params

    details = _get_search_details()
    extra_vars[u'fields'] = details[u'fields']
    extra_vars[u'fields_grouped'] = details[u'fields_grouped']
    search_extras = details[u'search_extras']

    admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')

    # context = {
    #     u'model': model,
    #     u'session': model.Session,
    #     u'user': admin_user,
    #     u'for_view': True,
    #     u'auth_user_obj': model.User.by_name(admin_user)
    # }

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'auth_user_obj': g.userobj
    }

    q += u' +dataset_type:{type} +creator_user_id:{sysadmin} +request_state:{state}'.format(type=package_type, sysadmin=_extra_template_variables(context,{'id':admin_user})['user_dict']['id'], state=request_state)

    facets = OrderedDict()

    # Facet titles
    for plugin in plugins.PluginImplementations(plugins.IFacets):
        facets = plugin.dataset_facets(facets, package_type)

    extra_vars[u'facet_titles'] = facets

    data_dict = {
        u'q': q,
        u'facet.field': list(facets.keys()),
        u'rows': limit,
        u'start': (page - 1) * limit,
        u'sort': sort_by,
        u'extras': search_extras,
        u'include_private': asbool(
            config.get(u'ckan.search.default_include_private', True)
        ),
    }

    try:
        query = plugins.toolkit.get_action('package_search')(context, data_dict)

        extra_vars[u'sort_by_selected'] = query[u'sort']

        extra_vars[u'page'] = h.Page(
            collection=query[u'results'],
            page=page,
            url=pager_url,
            item_count=query[u'count'],
            items_per_page=limit
        )
        extra_vars[u'search_facets'] = query[u'search_facets']
        extra_vars[u'page'].items = query[u'results']
    except SearchQueryError as se:
        # User's search parameters are invalid, in such a way that is not
        # achievable with the web interface, so return a proper error to
        # discourage spiders which are the main cause of this.
        log.info(u'Dataset search query rejected: %r', se.args)
        base.abort(
            400,
            _(u'Invalid search query: {error_message}')
            .format(error_message=str(se))
        )
    except SearchError as se:
        # May be bad input from the user, but may also be more serious like
        # bad code causing a SOLR syntax error, or a problem connecting to
        # SOLR
        log.error(u'Dataset search error: %r', se.args)
        extra_vars[u'query_error'] = True
        extra_vars[u'search_facets'] = {}
        extra_vars[u'page'] = h.Page(collection=[])
    
    # FIXME: try to avoid using global variables
    g.search_facets_limits = {}
    for facet in extra_vars[u'search_facets'].keys():
        try:
            limit = int(
                request.args.get(
                    u'_%s_limit' % facet,
                    int(config.get(u'search.facets.default', 10))
                )
            )
        except ValueError:
            base.abort(
                400,
                _(u'Parameter u"{parameter_name}" is not '
                  u'an integer').format(parameter_name=u'_%s_limit' % facet)
            )

        g.search_facets_limits[facet] = limit

    extra_vars[u'dataset_type'] = package_type

    # TODO: remove
    for key, value in six.iteritems(extra_vars):
        setattr(g, key, value)

    return extra_vars

def requestdata_receive_wait_maintainer_notify(request_state = u'requestdata_wait_maintainer_notify'):
    extra_vars = _requestdata_receive('receive_state_wait_maintainer_notify', request_state)

    return toolkit.render('requestdata/receive.html',
                           extra_vars=extra_vars)

def requestdata_receive_wait_received(request_state = u'requestdata_wait_received'):
    extra_vars = _requestdata_receive('receive_state_wait_received', request_state)

    return toolkit.render('requestdata/receive.html',
                           extra_vars=extra_vars)

def _requestdata_finished(page_url_type, request_state):
    package_type = u'requestdata'
    extra_vars = {}
    extra_vars['request_state'] = request_state

    try:
        context = dict(model=model, user=g.user, auth_user_obj=g.userobj)
        logic.check_access(u'steward', context)
    except logic.NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))

    extra_vars[u'q'] = q = request.args.get(u'q', u'')

    extra_vars['query_error'] = False
    page = h.get_page_number(request.args)

    limit = int(config.get(u'ckan.datasets_per_page', 20))

    params_nopage = [(k, v) for k, v in request.args.items(multi=True)
                     if k != u'page']

    extra_vars[u'drill_down_url'] = drill_down_url
    extra_vars[u'remove_field'] = partial(remove_field, package_type)

    sort_by = request.args.get(u'sort', None)
    params_nosort = [(k, v) for k, v in params_nopage if k != u'sort']

    extra_vars[u'sort_by'] = partial(_sort_by, params_nosort, package_type)

    if not sort_by:
        sort_by_fields = []
    else:
        sort_by_fields = [field.split()[0] for field in sort_by.split(u',')]
    extra_vars[u'sort_by_fields'] = sort_by_fields

    pager_url = partial(_pager_url, params_nopage, page_url_type)

    search_url_params = urlencode(_encode_params(params_nopage))
    extra_vars[u'search_url_params'] = search_url_params

    details = _get_search_details()
    extra_vars[u'fields'] = details[u'fields']
    extra_vars[u'fields_grouped'] = details[u'fields_grouped']
    search_extras = details[u'search_extras']

    admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')

    # context = {
    #     u'model': model,
    #     u'session': model.Session,
    #     u'user': admin_user,
    #     u'for_view': True,
    #     u'auth_user_obj': model.User.by_name(admin_user)
    # }

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'auth_user_obj': g.userobj
    }

    q += u' +dataset_type:{type} +creator_user_id:{sysadmin} +request_state:{state}'.format(type=package_type, sysadmin=_extra_template_variables(context,{'id':admin_user})['user_dict']['id'], state=request_state)

    facets = OrderedDict()

    # Facet titles
    for plugin in plugins.PluginImplementations(plugins.IFacets):
        facets = plugin.dataset_facets(facets, package_type)

    extra_vars[u'facet_titles'] = facets

    data_dict = {
        u'q': q,
        u'facet.field': list(facets.keys()),
        u'rows': limit,
        u'start': (page - 1) * limit,
        u'sort': sort_by,
        u'extras': search_extras,
        u'include_private': asbool(
            config.get(u'ckan.search.default_include_private', True)
        ),
    }

    try:
        query = plugins.toolkit.get_action('package_search')(context, data_dict)

        extra_vars[u'sort_by_selected'] = query[u'sort']

        extra_vars[u'page'] = h.Page(
            collection=query[u'results'],
            page=page,
            url=pager_url,
            item_count=query[u'count'],
            items_per_page=limit
        )
        extra_vars[u'search_facets'] = query[u'search_facets']
        extra_vars[u'page'].items = query[u'results']
    except SearchQueryError as se:
        # User's search parameters are invalid, in such a way that is not
        # achievable with the web interface, so return a proper error to
        # discourage spiders which are the main cause of this.
        log.info(u'Dataset search query rejected: %r', se.args)
        base.abort(
            400,
            _(u'Invalid search query: {error_message}')
            .format(error_message=str(se))
        )
    except SearchError as se:
        # May be bad input from the user, but may also be more serious like
        # bad code causing a SOLR syntax error, or a problem connecting to
        # SOLR
        log.error(u'Dataset search error: %r', se.args)
        extra_vars[u'query_error'] = True
        extra_vars[u'search_facets'] = {}
        extra_vars[u'page'] = h.Page(collection=[])
    
    # FIXME: try to avoid using global variables
    g.search_facets_limits = {}
    for facet in extra_vars[u'search_facets'].keys():
        try:
            limit = int(
                request.args.get(
                    u'_%s_limit' % facet,
                    int(config.get(u'search.facets.default', 10))
                )
            )
        except ValueError:
            base.abort(
                400,
                _(u'Parameter u"{parameter_name}" is not '
                  u'an integer').format(parameter_name=u'_%s_limit' % facet)
            )

        g.search_facets_limits[facet] = limit

    extra_vars[u'dataset_type'] = package_type

    # TODO: remove
    for key, value in six.iteritems(extra_vars):
        setattr(g, key, value)

    return extra_vars

def requestdata_finished_received(request_state = u'requestdata_received'):
    extra_vars = _requestdata_finished('finished_state_received', request_state)

    return toolkit.render('requestdata/finished.html',
                           extra_vars=extra_vars)

def requestdata_finished_reject(request_state = u'requestdata_reject'):
    extra_vars = _requestdata_finished('finished_state_reject', request_state)

    return toolkit.render('requestdata/finished.html',
                           extra_vars=extra_vars)

def _governance_processing(page_url_type, governance_state):
    package_type = u'processing'
    extra_vars = {}
    extra_vars['governance_state'] = governance_state

    try:
        context = dict(model=model, user=g.user, auth_user_obj=g.userobj)
        logic.check_access(u'steward', context)
    except logic.NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))

    extra_vars[u'q'] = q = request.args.get(u'q', u'')

    extra_vars['query_error'] = False
    page = h.get_page_number(request.args)

    limit = int(config.get(u'ckan.datasets_per_page', 20))

    params_nopage = [(k, v) for k, v in request.args.items(multi=True)
                     if k != u'page']

    extra_vars[u'drill_down_url'] = drill_down_url
    extra_vars[u'remove_field'] = partial(remove_field, package_type)

    sort_by = request.args.get(u'sort', None)
    params_nosort = [(k, v) for k, v in params_nopage if k != u'sort']

    extra_vars[u'sort_by'] = partial(_sort_by, params_nosort, package_type)

    if not sort_by:
        sort_by_fields = []
    else:
        sort_by_fields = [field.split()[0] for field in sort_by.split(u',')]
    extra_vars[u'sort_by_fields'] = sort_by_fields

    pager_url = partial(_pager_url, params_nopage, page_url_type)

    search_url_params = urlencode(_encode_params(params_nopage))
    extra_vars[u'search_url_params'] = search_url_params

    details = _get_search_details()
    extra_vars[u'fields'] = details[u'fields']
    extra_vars[u'fields_grouped'] = details[u'fields_grouped']
    search_extras = details[u'search_extras']

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'auth_user_obj': g.userobj
    }

    q += u' +dataset_type:{type} +governance_state:{state}'.format(type=package_type, state=governance_state)

    facets = OrderedDict()

    # Facet titles
    for plugin in plugins.PluginImplementations(plugins.IFacets):
        facets = plugin.dataset_facets(facets, package_type)

    extra_vars[u'facet_titles'] = facets

    data_dict = {
        u'q': q,
        u'facet.field': list(facets.keys()),
        u'rows': limit,
        u'start': (page - 1) * limit,
        u'sort': sort_by,
        u'extras': search_extras,
        u'include_private': asbool(
            config.get(u'ckan.search.default_include_private', True)
        ),
    }
    try:
        query = plugins.toolkit.get_action('package_search')(context, data_dict)

        extra_vars[u'sort_by_selected'] = query[u'sort']

        extra_vars[u'page'] = h.Page(
            collection=query[u'results'],
            page=page,
            url=pager_url,
            item_count=query[u'count'],
            items_per_page=limit
        )
        extra_vars[u'search_facets'] = query[u'search_facets']
        extra_vars[u'page'].items = query[u'results']
    except SearchQueryError as se:
        # User's search parameters are invalid, in such a way that is not
        # achievable with the web interface, so return a proper error to
        # discourage spiders which are the main cause of this.
        log.info(u'Dataset search query rejected: %r', se.args)
        base.abort(
            400,
            _(u'Invalid search query: {error_message}')
            .format(error_message=str(se))
        )
    except SearchError as se:
        # May be bad input from the user, but may also be more serious like
        # bad code causing a SOLR syntax error, or a problem connecting to
        # SOLR
        log.error(u'Dataset search error: %r', se.args)
        extra_vars[u'query_error'] = True
        extra_vars[u'search_facets'] = {}
        extra_vars[u'page'] = h.Page(collection=[])
    
    # FIXME: try to avoid using global variables
    g.search_facets_limits = {}
    for facet in extra_vars[u'search_facets'].keys():
        try:
            limit = int(
                request.args.get(
                    u'_%s_limit' % facet,
                    int(config.get(u'search.facets.default', 10))
                )
            )
        except ValueError:
            base.abort(
                400,
                _(u'Parameter u"{parameter_name}" is not '
                  u'an integer').format(parameter_name=u'_%s_limit' % facet)
            )

        g.search_facets_limits[facet] = limit

    extra_vars[u'dataset_type'] = package_type

    # TODO: remove
    for key, value in six.iteritems(extra_vars):
        setattr(g, key, value)

    return extra_vars

def governance_processing_wait(governance_state = u'wait'):
    extra_vars = _governance_processing('processing_state_wait', governance_state)

    return toolkit.render('governance/processing.html',
                           extra_vars=extra_vars)

def governance_processing_approval(governance_state = u'approval'):
    extra_vars = _governance_processing('processing_state_approval', governance_state)

    return toolkit.render('governance/processing.html',
                           extra_vars=extra_vars)

def _governance_finished(page_url_type, governance_state):
    package_type = u'processing'
    extra_vars = {}
    extra_vars['governance_state'] = governance_state

    try:
        context = dict(model=model, user=g.user, auth_user_obj=g.userobj)
        logic.check_access(u'steward', context)
    except logic.NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))

    extra_vars[u'q'] = q = request.args.get(u'q', u'')

    extra_vars['query_error'] = False
    page = h.get_page_number(request.args)

    limit = int(config.get(u'ckan.datasets_per_page', 20))

    params_nopage = [(k, v) for k, v in request.args.items(multi=True)
                     if k != u'page']

    extra_vars[u'drill_down_url'] = drill_down_url
    extra_vars[u'remove_field'] = partial(remove_field, package_type)

    sort_by = request.args.get(u'sort', None)
    params_nosort = [(k, v) for k, v in params_nopage if k != u'sort']

    extra_vars[u'sort_by'] = partial(_sort_by, params_nosort, package_type)

    if not sort_by:
        sort_by_fields = []
    else:
        sort_by_fields = [field.split()[0] for field in sort_by.split(u',')]
    extra_vars[u'sort_by_fields'] = sort_by_fields

    pager_url = partial(_pager_url, params_nopage, page_url_type)

    search_url_params = urlencode(_encode_params(params_nopage))
    extra_vars[u'search_url_params'] = search_url_params

    details = _get_search_details()
    extra_vars[u'fields'] = details[u'fields']
    extra_vars[u'fields_grouped'] = details[u'fields_grouped']
    search_extras = details[u'search_extras']

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'auth_user_obj': g.userobj
    }

    q += u' +dataset_type:{type} +governance_state:{state} +previous_governance_state:["" TO *]'.format(type=package_type, state=governance_state)

    facets = OrderedDict()

    # Facet titles
    for plugin in plugins.PluginImplementations(plugins.IFacets):
        facets = plugin.dataset_facets(facets, package_type)

    extra_vars[u'facet_titles'] = facets

    data_dict = {
        u'q': q,
        u'facet.field': list(facets.keys()),
        u'rows': limit,
        u'start': (page - 1) * limit,
        u'sort': sort_by,
        u'extras': search_extras,
        u'include_private': asbool(
            config.get(u'ckan.search.default_include_private', True)
        ),
    }
    try:
        query = plugins.toolkit.get_action('package_search')(context, data_dict)
        
        if governance_state == 'reject':
            for result_pkg in query[u'results']:
                try:
                    prepare_result = plugins.toolkit.get_action('package_show')(None, {'id':result_pkg['prepare_dataset_id']})
                    if prepare_result['state'] == 'deleted':
                        result_pkg['processing'] = 'not found'
                    elif prepare_result['type'] == 'dataset':
                        result_pkg['processing'] = 'finished'
                    elif prepare_result['type'] == 'prepare':
                        if 'processing_dataset_id' in prepare_result and prepare_result['processing_dataset_id'] != '':
                            result_pkg['processing'] = prepare_result['processing_dataset_id']
                        else:
                            result_pkg['processing'] = ''
                except NotFound:
                    result_pkg['processing'] = 'not found'

        extra_vars[u'sort_by_selected'] = query[u'sort']

        extra_vars[u'page'] = h.Page(
            collection=query[u'results'],
            page=page,
            url=pager_url,
            item_count=query[u'count'],
            items_per_page=limit
        )
        extra_vars[u'search_facets'] = query[u'search_facets']
        extra_vars[u'page'].items = query[u'results']
    except SearchQueryError as se:
        # User's search parameters are invalid, in such a way that is not
        # achievable with the web interface, so return a proper error to
        # discourage spiders which are the main cause of this.
        log.info(u'Dataset search query rejected: %r', se.args)
        base.abort(
            400,
            _(u'Invalid search query: {error_message}')
            .format(error_message=str(se))
        )
    except SearchError as se:
        # May be bad input from the user, but may also be more serious like
        # bad code causing a SOLR syntax error, or a problem connecting to
        # SOLR
        log.error(u'Dataset search error: %r', se.args)
        extra_vars[u'query_error'] = True
        extra_vars[u'search_facets'] = {}
        extra_vars[u'page'] = h.Page(collection=[])

    # FIXME: try to avoid using global variables
    g.search_facets_limits = {}
    for facet in extra_vars[u'search_facets'].keys():
        try:
            limit = int(
                request.args.get(
                    u'_%s_limit' % facet,
                    int(config.get(u'search.facets.default', 10))
                )
            )
        except ValueError:
            base.abort(
                400,
                _(u'Parameter u"{parameter_name}" is not '
                  u'an integer').format(parameter_name=u'_%s_limit' % facet)
            )

        g.search_facets_limits[facet] = limit

    extra_vars[u'dataset_type'] = package_type

    # TODO: remove
    for key, value in six.iteritems(extra_vars):
        setattr(g, key, value)

    return extra_vars

def governance_finished_complete(governance_state = u'complete'):
    extra_vars = _governance_finished('finished_state_complete', governance_state)

    return toolkit.render('governance/finished.html',
                           extra_vars=extra_vars)

def governance_finished_reject(governance_state = u'reject'):
    extra_vars = _governance_finished('finished_state_reject', governance_state)

    return toolkit.render('governance/finished.html',
                           extra_vars=extra_vars)

def requestdata_agreement(package_id):

    already = _check_already_requestdata(package_id)
    # check if package exists
    try:
        pkg_dict = plugins.toolkit.get_action('package_show')(None, {'id':package_id})
    except (NotFound, NotAuthorized):
        return base.abort(404, _(u'Dataset not found'))

    return base.render(
            'requestdata/new_form.html', {
                u'pkg': pkg_dict,
                u'confirm': False,
                u'already': already,
            })

def _check_already_requestdata(package_id):
    admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }

    try:
        user_dict = plugins.toolkit.get_action('user_show')(context, {'id':g.user, 'include_plugin_extras':True})
    except (NotFound, NotAuthorized):
        return base.abort(404, _(u'Dataset not found'))

    already_req = plugins.toolkit.get_action('package_search')(context, {"q":"type:requestdata +requester_id:"+user_dict['id']+" +package_id:"+package_id,"include_private":True,"rows":1})
    log.info('check already_req')
    if already_req['count']:
        dt = datetime.datetime.now()
        d2 = datetime.datetime.strptime(dt.strftime("%Y%m%d%H%M%S"), '%Y%m%d%H%M%S')
        d1 = datetime.datetime.strptime(already_req['results'][0]['name'][0:14], '%Y%m%d%H%M%S')
        if abs((d2 - d1).days) < 1:
            log.info('do not send request')
            return True
    return False

def requestdata_received(request_id):

    admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }

    # check if package exists
    try:
        req_dict = plugins.toolkit.get_action('package_show')(context, {'id':request_id})
    except (NotFound, NotAuthorized):
        return base.abort(404, _(u'Dataset not found'))
    
    data = request.form.to_dict()
    if 'save' in data:
        try:
            # really?
            post_data_dict = logic.clean_dict(dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form))))

            del post_data_dict['save']
            
            data_dict = {'id':request_id, 'request_state': post_data_dict['request_state'], 'received_date':post_data_dict['received_date'], 'steward_from_wait_received':g.userobj.id}
            plugins.toolkit.get_action('package_patch')(context, data_dict)

            return base.render(
                'requestdata/received_form.html', {
                    u'pkg': req_dict,
                    u'completed': True,
                    u'received_date': post_data_dict['received_date']
                })
            
        except logic.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return base.render(
                'requestdata/received_form.html', {
                    u'pkg': req_dict,
                    u'completed': False
                })

    return base.render(
            'requestdata/received_form.html', {
                u'pkg': req_dict,
                u'completed': False
            })

def requestdata_notified(request_id):

    admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }

    # check if package exists
    try:
        req_dict = plugins.toolkit.get_action('package_show')(context, {'id':request_id})
    except (NotFound, NotAuthorized):
        return base.abort(404, _(u'Dataset not found'))
    
    data = request.form.to_dict()
    if 'save' in data:
        try:
            # really?
            post_data_dict = logic.clean_dict(dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form))))

            del post_data_dict['save']
            
            data_dict = {'id':request_id, 'request_state': post_data_dict['request_state'], 'maintainer_notify_date':post_data_dict['maintainer_notify_date'], 'steward_from_wait_maintainer_notify':g.userobj.id}
            plugins.toolkit.get_action('package_patch')(context, data_dict)

            return base.render(
                'requestdata/notified_form.html', {
                    u'pkg': req_dict,
                    u'completed': True,
                    u'maintainer_notify_date': post_data_dict['maintainer_notify_date']
                })
            
        except logic.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return base.render(
                'requestdata/notified_form.html', {
                    u'pkg': req_dict,
                    u'completed': False
                })

    return base.render(
            'requestdata/notified_form.html', {
                u'pkg': req_dict,
                u'completed': False
            })

def _create_prepare(context, package_id):
    log.info('_create_prepare '+str(package_id))
    pkg_dict_create = ""
    try:
        pkg_dict = plugins.toolkit.get_action('package_show')(context, {'id':package_id}) #get dataset
        pkg_dict_original = pkg_dict.copy()
        
        pkg_dict['type'] = 'prepare'

        pkg_dict['name'] = 'gprepare-'+pkg_dict['name']
        pkg_dict['publish_dataset_id'] = pkg_dict['id']
        del pkg_dict['id']
        pkg_dict['extras'] = pkg_dict.get('extras',[])
        del pkg_dict['extras']

        if pkg_dict['num_resources'] > 0 :
            del pkg_dict['resources']

        context = dict(model=model, user=g.user, auth_user_obj=g.userobj)
        pkg_dict_create = plugins.toolkit.get_action('package_create')(context, pkg_dict)
        if pkg_dict_original['num_resources'] > 0 :
            for resourceDict in pkg_dict_original['resources']:
                resourceDict['package_id'] = pkg_dict_create['id']
                resourceDict['publish_resource_id'] = resourceDict['id']
                del resourceDict['id']
                resourceDict['convert_file'] = resourceDict.get('convert_file',[])
                del resourceDict['convert_file']
                resourceDict['url_type'] = resourceDict.get('url_type',[])
                del resourceDict['url_type']
                resourceDict['datastore_active'] = resourceDict.get('datastore_active',[])
                del resourceDict['datastore_active']
                if config.get('ckan.site_url')+'/dataset/' in resourceDict['url']:
                    resourceDict['url'] = resourceDict['url'].rsplit('/', 1)[1]
                    resourceDict['url_type'] = 'upload'
                    resourceDict['hash'] = ''
                    res_created = plugins.toolkit.get_action('resource_create')(context, resourceDict) # create resources in prepare
                    try:
                        os.makedirs(config.get('ckan.storage_path')+'/resources/'+res_created['id'][0:3]+'/'+res_created['id'][3:6])
                        os.popen('cp '+config.get('ckan.storage_path')+'/resources/'+resourceDict['publish_resource_id'][0:3]+'/'+resourceDict['publish_resource_id'][3:6]+'/'+resourceDict['publish_resource_id'][6:]+' '+config.get('ckan.storage_path')+'/resources/'+res_created['id'][0:3]+'/'+res_created['id'][3:6]+'/'+res_created['id'][6:])
                    except OSError as e:
                        # errno 17 is file already exists
                        if e.errno != 17:
                            raise
                else:
                    resourceDict['hash'] = ''
                    res_created = plugins.toolkit.get_action('resource_create')(context, resourceDict) # create resources in prepare
    except:
        raise ValidationError
    return pkg_dict_create

def _create_processing(context, package_id):
    pkg_dict_create = ""
    try:
        pkg_dict = plugins.toolkit.get_action('package_show')(context, {'id':package_id}) #get prepare
        pkg_dict_original = pkg_dict.copy()
        
        pkg_dict['type'] = 'processing'
        pkg_dict['governance_state'] = 'wait'
        pkg_dict['governance_disclosure'] = pkg_dict['disclosure']
        pkg_dict['governance_data_category'] = pkg_dict['data_category']
        pkg_dict['governance_allow_harvest'] = pkg_dict['allow_harvest']
        
        pkg_dict['prepare_dataset_id'] = package_id
        dt = datetime.datetime.now()
        if pkg_dict['name'].startswith('gprepare-') and pkg_dict.get('publish_dataset_id','') != '':
            name_tmp = pkg_dict['name'].replace('gprepare-','')
            pkg_dict['name'] = 'gprocessing-'+dt.strftime("%Y%m%d%H%M%S")+'-'+name_tmp
        else:
            pkg_dict['name'] = 'gprocessing-'+dt.strftime("%Y%m%d%H%M%S")+'-'+pkg_dict['name']
        del pkg_dict['id']

        if pkg_dict['num_resources'] > 0 :
            del pkg_dict['resources']

        user_obj = model.User.get(six.ensure_text(pkg_dict['creator_user_id']))
        context = {'model': model, 'session': model.Session, 'ignore_auth': True,
                'user': user_obj.name, 'auth_user_obj': None}
        pkg_dict_create = plugins.toolkit.get_action('package_create')(context, pkg_dict)
        if pkg_dict_original['num_resources'] > 0 :
            for resourceDict in pkg_dict_original['resources']:
                resourceDict['package_id'] = pkg_dict_create['id']
                resourceDict['prepare_resource_id'] = resourceDict['id']
                del resourceDict['id']
                resourceDict['convert_file'] = resourceDict.get('convert_file',[])
                del resourceDict['convert_file']
                resourceDict['url_type'] = resourceDict.get('url_type',[])
                del resourceDict['url_type']
                resourceDict['datastore_active'] = resourceDict.get('datastore_active',[])
                del resourceDict['datastore_active']
                if config.get('ckan.site_url')+'/dataset/' in resourceDict['url']:
                    resourceDict['url'] = config.get('ckan.site_url')+'/dataset/'+resourceDict['url'].split('/dataset/')[1]
                else:
                    resourceDict['url'] = ''
                plugins.toolkit.get_action('resource_create')(context, resourceDict) # create resources in processing
    except:
        raise ValidationError
    return pkg_dict_create

def dataset_toprepare(package_id):
    pakcgae_obj = model.Package.get(package_id)
    if not pakcgae_obj:
        return base.abort(404, _(u'Dataset not found'))
    user_obj = model.User.get(pakcgae_obj.creator_user_id)
    current_user_obj = model.User.get(g.user)
    if user_obj != current_user_obj:
        return base.abort(404, _(u'Dataset not found'))

    log.info('dataset_toprepare '+str(package_id))

    admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }

    # check if package exists
    try:
        pkg_dict = plugins.toolkit.get_action('package_show')(context, {'id':package_id})
    except (NotFound, NotAuthorized):
        return base.abort(404, _(u'Dataset not found'))
    
    already_prepare = plugins.toolkit.get_action('package_search')(context, {"q":"type:prepare +publish_dataset_id:"+pkg_dict['id'],"include_private":True,"rows":1})

    if pkg_dict['type'] == 'dataset' and already_prepare['count'] == 0:
        pkg_prepare_return = _create_prepare(context, package_id) #create prepare
    else:
        return base.abort(404, _(u'Dataset not found'))
    return h.redirect_to('/prepare/'+pkg_prepare_return['id'])

def prepare_toprocess(package_id):
    log.info('prepare_toprocess '+str(package_id))

    admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }

    # check if package exists
    try:
        pkg_dict = plugins.toolkit.get_action('package_show')(context, {'id':package_id})
        if pkg_dict['disclosure'] != 'public' and pkg_dict['disclosure'] != 'registered' and pkg_dict['num_resources'] > 0:
            return base.abort(
                    403, _(u'ไม่สามารถส่งเรื่องเพื่อพิจารณาชุดข้อมูลได้ กรุณาลบไฟล์ทรัพยากร เพื่อให้สอดคล้องกับระดับชั้นข้อมูลที่ท่านเลือก')
                )
    except (NotFound, NotAuthorized):
        return base.abort(404, _(u'Dataset not found'))

    pkg_dict_update = ''

    processing_dataset_id = pkg_dict.get('processing_dataset_id','')
    if pkg_dict['type'] == 'prepare' and (processing_dataset_id=='' or processing_dataset_id=='finished'):
        pkg_processing_return = _create_processing(context, package_id) #create processing

        pkg_dict_update = plugins.toolkit.get_action('package_patch')(context, {"id":package_id, "processing_dataset_id":pkg_processing_return['id']}) #update prepare
        portal = LocalCKAN()
        activity_dict = {"data": {"actor": six.ensure_text(c.user), "package":pkg_dict_update, 
            "governance": {"governance_log":"Change prepare to processing","governance_state":"wait","governance_notes":"-","governance_steward":"","governance_date":""}}, 
            "user_id": pkg_dict_update.get("creator_user_id"), 
            "object_id": pkg_dict_update.get("id"), 
            "activity_type": "changed package"
            }
        portal.action.activity_create(**activity_dict)

        myobj = {"user_id": pkg_dict['creator_user_id'],"package_id": pkg_dict['id'],"event":"owner_submit_forowner"}
        plugins.toolkit.get_action('governance_send_mail')(context, myobj)
        
        myobj = {"user_id": pkg_dict['creator_user_id'],"package_id": pkg_dict['id'],"event":"owner_submit_forsteward"}
        plugins.toolkit.get_action('governance_send_mail')(context, myobj)
    else:
        raise NotFound
    return h.redirect_to('/prepare/'+package_id)

def requestdata_new(package_id, data=None, errors=None, error_summary=None):
    admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')
    
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }

    # check if package exists
    try:
        pkg_dict = plugins.toolkit.get_action('package_show')(None, {'id':package_id})

        owner_org_dict = plugins.toolkit.get_action('organization_show')(None, {'id':pkg_dict['owner_org']}) #get organization of package
    except (NotFound, NotAuthorized):
        return base.abort(404, _(u'Dataset not found'))
    
    # check if user exists
    try:
        user_dict = plugins.toolkit.get_action('user_show')(context, {'id':g.user, 'include_plugin_extras':True})
    except (NotFound, NotAuthorized):
        return base.abort(404, _(u'Dataset not found'))

    data = request.form.to_dict()
    if 'save' in data:
        try:
            # really?
            post_data_dict = logic.clean_dict(dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form))))

            del post_data_dict['save']
            
            dt = datetime.datetime.now()
            post_data_dict['name'] = dt.strftime("%Y%m%d%H%M%S")+'_'+str(uuid.uuid4())
            post_data_dict['package_id'] = package_id
            post_data_dict['package_owner'] = pkg_dict['creator_user_id']
            post_data_dict['title'] = dt.strftime("%Y%m%d%H%M%S")+'-'+pkg_dict['title']
            post_data_dict['owner_org'] = pkg_dict['owner_org']
            post_data_dict['requester_id'] = user_dict['id']
            post_data_dict['request_state'] = u'requestdata_wait_steward'
            post_data_dict['type'] = 'requestdata'
            post_data_dict['private'] = True

            already_req = plugins.toolkit.get_action('package_search')(context, {"q":"type:requestdata +requester_id:"+user_dict['id']+" +package_id:"+package_id,"include_private":True,"rows":1})
            log.info('check already_req')
            if already_req['count']: 
                d2 = datetime.datetime.strptime(dt.strftime("%Y%m%d%H%M%S"), '%Y%m%d%H%M%S')
                d1 = datetime.datetime.strptime(already_req['results'][0]['name'][0:14], '%Y%m%d%H%M%S')
                if abs((d2 - d1).days) < 1:
                    log.info('do not send request')
                    return toolkit.render('requestdata/confirm_send.html')

            requestdata = plugins.toolkit.get_action('package_create')(context, post_data_dict)

            myobj = {"user_id": user_dict['id'],"package_id": package_id,"event":"requestdata_forrequester"}
            plugins.toolkit.get_action('governance_send_mail')(context, myobj)

            myobj = {"user_id": user_dict['id'],"package_id": package_id,"request_id": requestdata['id'],"event":"requestdata_forsteward"}
            plugins.toolkit.get_action('governance_send_mail')(context, myobj)

            return toolkit.render('requestdata/confirm_send.html')
            
        except logic.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return base.render(
            'requestdata/new_form.html', {
                u'pkg': pkg_dict,
                u'user': user_dict,
                u'data': data or {},
                u'errors': errors or {},
                u'error_summary': error_summary or {},
                u'confirm': True,
                u'already': False,
            })
    
    already = _check_already_requestdata(package_id)

    template = 'requestdata/new_form.html'
    try:
        return base.render(
            template, {
                u'pkg': pkg_dict,
                u'user': user_dict,
                u'data': data or {},
                u'errors': errors or {},
                u'error_summary': error_summary or {},
                u'confirm': True,
                u'already': already,
            }
        )
    except TemplateNotFound as e:
        msg = 'not found'
        return base.abort(404, msg)

    assert False, u"We should never get here"

def processing_package_read():
    id = request.params['id']
    package_type = u'dataset'

    try:
        context = dict(model=model, user=g.user, auth_user_obj=g.userobj)
        logic.check_access(u'steward', context)
    except logic.NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))
    
    admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')
    
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }
    
    data = request.form.to_dict()
    if 'save' in data:
        try:
            # really?
            post_data_dict = logic.clean_dict(dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form))))

            del post_data_dict['save']
            
            if 'governance_allow_harvest' in post_data_dict:
                data_dict = {'id':id, 'governance_data_category': post_data_dict['governance_data_category'], 'governance_state':post_data_dict['governance_state'], 'governance_disclosure':post_data_dict['governance_disclosure'], 'governance_allow_harvest':post_data_dict['governance_allow_harvest'], 'governance_notes':post_data_dict['governance_notes'], 'governance_steward':g.userobj.id, 'governance_date':post_data_dict['governance_date']}
            else:
                data_dict = {'id':id, 'governance_data_category': post_data_dict['governance_data_category'], 'governance_state':post_data_dict['governance_state'], 'governance_disclosure':post_data_dict['governance_disclosure'], 'governance_notes':post_data_dict['governance_notes'], 'governance_steward':g.userobj.id, 'governance_date':post_data_dict['governance_date']}
            pkg_processing_dict = plugins.toolkit.get_action('processing_update_state')(context, data_dict)
            url = '/governance/processing_state_'+pkg_processing_dict['previous_governance_state']

            return h.redirect_to(url)
            
        except logic.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return h.redirect_to('/governance/processing_state')
            #vars = {'data': data, 'errors': errors,
            #        'error_summary': error_summary}
            #return render('governance/processing.html', extra_vars=vars)
    elif 'save_publish' in data:
        from ckan.lib.search import rebuild
        try:
            post_data_dict = logic.clean_dict(dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form))))

            del post_data_dict['save_publish']

            user_obj = model.User.get(six.ensure_text(post_data_dict['creator_user_id']))

            data_dict = {'id':id, 'post_publish_governance_data_category': post_data_dict['post_publish_governance_data_category'], 'post_publish_governance_disclosure':post_data_dict['post_publish_governance_disclosure'], 'post_publish_governance_allow_harvest':post_data_dict['post_publish_governance_allow_harvest'], 'post_publish_governance_state': post_data_dict['post_publish_governance_state'], 'post_publish_governance_notes':post_data_dict['post_publish_governance_notes'], 'post_publish_governance_steward':g.userobj.id, 'maintainer':post_data_dict['maintainer'], 'maintainer_email':post_data_dict['maintainer_email']}
            pkg_processing_dict = plugins.toolkit.get_action('package_patch')(context, data_dict)

            data_dict = {'id':pkg_processing_dict['prepare_dataset_id'], 'data_category': post_data_dict['post_publish_governance_data_category'], 'disclosure':post_data_dict['post_publish_governance_disclosure'], 'allow_harvest':post_data_dict['post_publish_governance_allow_harvest'], 'maintainer':post_data_dict['maintainer'], 'maintainer_email':post_data_dict['maintainer_email']}
            pkg_publish_dict = plugins.toolkit.get_action('package_patch')(context, data_dict)

            if user_obj:
                model.Session.query(model.Package).filter_by(id=pkg_processing_dict['id']).update({u'creator_user_id': post_data_dict['creator_user_id']})
                model.Session.commit()

                model.Session.query(model.Package).filter_by(id=pkg_processing_dict['prepare_dataset_id']).update({u'creator_user_id': post_data_dict['creator_user_id']})
                model.Session.commit()
            
            if post_data_dict['post_publish_governance_state'] == 'เพิกถอน':
                model.Session.query(model.Package).filter_by(id=pkg_processing_dict['prepare_dataset_id']).update({u'state': 'pending'})
                model.Session.commit()
            else:
                model.Session.query(model.Package).filter_by(id=pkg_processing_dict['prepare_dataset_id']).update({u'state': 'active'})
                model.Session.commit()
            
            rebuild(id)
            rebuild(pkg_processing_dict['prepare_dataset_id'])

            url = '/governance/finished_state_complete'

            return h.redirect_to(url)
            
        except logic.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return h.redirect_to('/governance/processing_state')

    data_dict = {u'id': id, u'include_tracking': True}

    # check if package exists
    try:
        pkg_dict = plugins.toolkit.get_action('package_show')(context, data_dict)
        pkg_dict_prepare = plugins.toolkit.get_action('package_show')(context, {u'id': pkg_dict['prepare_dataset_id']})
    except (NotFound, NotAuthorized):
        return base.abort(404, _(u'Dataset not found'))

    
    # can the resources be previewed?
    for resource in pkg_dict_prepare[u'resources']:
        resource_views = get_action(u'resource_view_list')(
            context, {
                u'id': resource[u'id']
            }
        )
        resource[u'has_views'] = len(resource_views) > 0

    if pkg_dict_prepare.get('publish_dataset_id','') == '':
        template = 'governance/package/read.html'
        if pkg_dict.get('post_publish_governance_data_category','') == '':
            pkg_dict['post_publish_governance_data_category'] = pkg_dict.get('governance_data_category',pkg_dict_prepare['data_category'])
        if pkg_dict.get('post_publish_governance_disclosure','') == '':
            pkg_dict['post_publish_governance_disclosure'] = pkg_dict.get('governance_disclosure',pkg_dict_prepare['disclosure'])
        if pkg_dict.get('post_publish_governance_allow_harvest','') == '':
            pkg_dict['post_publish_governance_allow_harvest'] = pkg_dict.get('governance_allow_harvest',pkg_dict_prepare['allow_harvest'])
        if pkg_dict.get('post_publish_governance_state','') == '':
            pkg_dict['post_publish_governance_state'] = u'เผยแพร่'
        pkg_dict_publish = None
    else:
        template = 'governance/package/read_modify.html'
        pkg_dict_publish = plugins.toolkit.get_action('package_show')(context, {u'id': pkg_dict_prepare['publish_dataset_id']})
    try:
        return base.render(
            template, {
                u'dataset_type': package_type,
                u'pkg_dict': pkg_dict,
                u'pkg_dict_prepare': pkg_dict_prepare,
                u'pkg_dict_publish': pkg_dict_publish,
            }
        )
    except TemplateNotFound as e:
        msg = _(
            u"Viewing datasets of type \"{package_type}\" is "
            u"not supported ({file_!r}).".format(
                package_type=package_type, file_=e.message
            )
        )
        return base.abort(404, msg)

    assert False, u"We should never get here"

def processing_requestdata_read():
    id = request.params['id']
    package_type = u'requestdata'

    try:
        context = dict(model=model, user=g.user, auth_user_obj=g.userobj)
        logic.check_access(u'steward', context)
    except logic.NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))
    
    data_dict = {u'id': id}

    # check if package exists
    try:
        admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')
    
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': admin_user,
            u'for_view': True,
            u'auth_user_obj': model.User.by_name(admin_user)
        }
        pkg_dict = plugins.toolkit.get_action('package_show')(context, data_dict)
        req_pkg_dict = plugins.toolkit.get_action('package_show')(context, {u'id': pkg_dict['package_id']})
    except (NotFound, NotAuthorized):
        return base.abort(404, _(u'Dataset not found'))
    
    data = request.form.to_dict()
    if 'save' in data:
        try:
            # really?
            post_data_dict = logic.clean_dict(dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form))))

            del post_data_dict['save']

            if post_data_dict['current_request_sate'] == 'requestdata_wait_steward':
                data_dict = {'id':id, 'request_state': post_data_dict['request_state'], 'steward_date':post_data_dict['steward_date'], 'steward_comment':post_data_dict['steward_comment'], 'summary_comment':post_data_dict['summary_comment'], 'steward_from_wait_steward':g.userobj.id}
                current_request_sate = 'requestdata_wait_steward'
                current_state = 'processing_state'
            elif post_data_dict['current_request_sate'] == 'requestdata_wait_council':
                data_dict = {'id':id, 'request_state': post_data_dict['request_state'], 'council_date':post_data_dict['council_date'], 'council_comment':post_data_dict['council_comment'], 'summary_comment':post_data_dict['summary_comment'], 'steward_from_wait_council':g.userobj.id}
                current_request_sate = 'requestdata_wait_council'
                current_state = 'processing_state'
            elif post_data_dict['current_request_sate'] == 'requestdata_wait_maintainer_notify':
                data_dict = {'id':id, 'request_state': post_data_dict['request_state'], 'maintainer_notify_date':post_data_dict['maintainer_notify_date'], 'steward_from_wait_maintainer_notify':g.userobj.id}
                current_request_sate = 'requestdata_wait_maintainer_notify'
                current_state = 'receive_state'
            elif post_data_dict['current_request_sate'] == 'requestdata_wait_received':
                data_dict = {'id':id, 'request_state': post_data_dict['request_state'], 'received_date':post_data_dict['received_date'], 'steward_from_wait_received':g.userobj.id}
                current_request_sate = 'requestdata_wait_received'
                current_state = 'receive_state'
            plugins.toolkit.get_action('package_patch')(context, data_dict)

            if post_data_dict['request_state'] == 'requestdata_wait_maintainer_notify':
                log.info('send_mail requestdata_wait_maintainer_notify')
                myobj = {"user_id": pkg_dict['requester_id'],"package_id": req_pkg_dict['id'],"event":"notify_requestdata_approval_forrequester"}
                plugins.toolkit.get_action('governance_send_mail')(context, myobj)
                myobj2 = {"user_id": pkg_dict['requester_id'],"package_id": req_pkg_dict['id'],"request_id":id,"event":"notify_requestdata_approval_forsteward"}
                plugins.toolkit.get_action('governance_send_mail')(context, myobj2)
            #elif post_data_dict['request_state'] == 'requestdata_wait_received':
                #log.info('send_mail requestdata_wait_received')
                myobj3 = {"user_id": pkg_dict['requester_id'],"package_id": req_pkg_dict['id'],"event":"notify_requestdata_approval_forowner"}
                plugins.toolkit.get_action('governance_send_mail')(context, myobj3)
            elif post_data_dict['request_state'] == 'requestdata_reject':
                log.info('send_mail requestdata_reject')
                myobj = {"user_id": pkg_dict['requester_id'],"package_id": req_pkg_dict['id'],"summary_comment": post_data_dict['summary_comment'],"event":"notify_requestdata_reject_forrequester"}
                plugins.toolkit.get_action('governance_send_mail')(context, myobj)

            url = '/governance/requestdata/'+current_state+'_'+current_request_sate.replace('requestdata_','')

            return h.redirect_to(url)
            
        except logic.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return h.redirect_to('/governance/requestdata/processing_state')
            #vars = {'data': data, 'errors': errors,
            #        'error_summary': error_summary}
            #return render('governance/processing.html', extra_vars=vars)

    template = 'governance/requestdata/read.html'
    try:
        return base.render(
            template, {
                u'dataset_type': package_type,
                u'pkg_dict': pkg_dict,
                u'req_pkg_dict': req_pkg_dict,
            }
        )
    except TemplateNotFound as e:
        msg = _(
            u"Viewing datasets of type \"{package_type}\" is "
            u"not supported ({file_!r}).".format(
                package_type=package_type, file_=e.message
            )
        )
        return base.abort(404, msg)

    assert False, u"We should never get here"



governance.add_url_rule(u'/governance', view_func=governance_processing_wait)

governance.add_url_rule(u'/governance/processing_state', view_func=governance_processing_wait)
governance.add_url_rule(u'/governance/processing_state_wait', view_func=governance_processing_wait)
governance.add_url_rule(u'/governance/processing_state_wait.search', view_func=governance_processing_wait)
governance.add_url_rule(u'/governance/processing_state_approval', view_func=governance_processing_approval)
governance.add_url_rule(u'/governance/processing_state_approval.search', view_func=governance_processing_approval)

governance.add_url_rule(u'/governance/finished_state', view_func=governance_finished_complete)
governance.add_url_rule(u'/governance/finished_state_complete', view_func=governance_finished_complete)
governance.add_url_rule(u'/governance/finished_state_complete.search', view_func=governance_finished_complete)
governance.add_url_rule(u'/governance/finished_state_reject', view_func=governance_finished_reject)
governance.add_url_rule(u'/governance/finished_state_reject.search', view_func=governance_finished_reject)

governance.add_url_rule(u'/governance/processing', view_func=processing_package_read, methods=["GET", "POST"])
governance.add_url_rule(u'/requestdata_form/<package_id>', view_func=requestdata_new, methods=["GET", "POST"])
governance.add_url_rule(u'/requestdata_agreement/<package_id>', view_func=requestdata_agreement)
governance.add_url_rule(u'/requestdata_received/<request_id>', view_func=requestdata_received, methods=["GET", "POST"])
governance.add_url_rule(u'/requestdata_notified/<request_id>', view_func=requestdata_notified, methods=["GET", "POST"])
governance.add_url_rule(u'/dashboard/requestdatas', view_func=my_requestdata_list)
governance.add_url_rule(u'/dashboard/requested_packages', view_func=my_package_requested_list)
governance.add_url_rule(u'/governance/requestdata', view_func=requestdata_processing_wait_steward)

governance.add_url_rule(u'/governance/requestdata/processing', view_func=processing_requestdata_read, methods=["GET", "POST"])

governance.add_url_rule(u'/governance/requestdata/processing_state', view_func=requestdata_processing_wait_steward)
governance.add_url_rule(u'/governance/requestdata/processing_state_wait_steward', view_func=requestdata_processing_wait_steward)
governance.add_url_rule(u'/governance/requestdata/processing_state_wait_steward.search', view_func=requestdata_processing_wait_steward)
governance.add_url_rule(u'/governance/requestdata/processing_state_wait_council', view_func=requestdata_processing_wait_council)
governance.add_url_rule(u'/governance/requestdata/processing_state_wait_council.search', view_func=requestdata_processing_wait_council)

governance.add_url_rule(u'/governance/requestdata/receive_state', view_func=requestdata_receive_wait_maintainer_notify)
governance.add_url_rule(u'/governance/requestdata/receive_state_wait_maintainer_notify', view_func=requestdata_receive_wait_maintainer_notify)
governance.add_url_rule(u'/governance/requestdata/receive_state_wait_maintainer_notify.search', view_func=requestdata_receive_wait_maintainer_notify)
governance.add_url_rule(u'/governance/requestdata/receive_state_wait_received', view_func=requestdata_receive_wait_received)
governance.add_url_rule(u'/governance/requestdata/receive_state_wait_received.search', view_func=requestdata_receive_wait_received)

governance.add_url_rule(u'/governance/requestdata/finished_state', view_func=requestdata_finished_received)
governance.add_url_rule(u'/governance/requestdata/finished_state_received', view_func=requestdata_finished_received)
governance.add_url_rule(u'/governance/requestdata/finished_state_received.search', view_func=requestdata_finished_received)
governance.add_url_rule(u'/governance/requestdata/finished_state_reject', view_func=requestdata_finished_reject)
governance.add_url_rule(u'/governance/requestdata/finished_state_reject.search', view_func=requestdata_finished_reject)

governance.add_url_rule(u'/governance/prepare_toprocess/<package_id>', view_func=prepare_toprocess)
governance.add_url_rule(u'/governance/dataset_toprepare/<package_id>', view_func=dataset_toprepare)
