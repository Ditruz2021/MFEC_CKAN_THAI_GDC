#!/usr/bin/env python
# encoding: utf-8

import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.model as model
from pylons import config
from ckan.common import _, c
import ckan.lib.helpers as h
import json
import os
import logging
import copy
import ckan.lib.dictization.model_dictize as model_dictize

from ckanext.thai_gdc.model.opend import OpendModel
import requests
from datetime import datetime as dt

get_action = logic.get_action
check_access = h.check_access
opend_model = OpendModel()

log = logging.getLogger(__name__)

def dataset_bulk_import_log(import_id):
    logs = opend_model.get_dataset_bulk_import_log(import_id)
    return logs

def dataset_bulk_import_status(import_id):
    try:
        context = {'model': model,
                    'user': c.user, 'auth_user_obj': c.userobj}

        like_q1 = u'%' + import_id + u'%'
        like_q2 = u'%Finished%'

        q = model.Session.query(model.Activity).filter(model.Activity.activity_type == 'changed user').filter(model.Activity.data.ilike(like_q1)).filter(model.Activity.data.ilike(like_q2))
        activities = q.all()
    except:
        return []

    return model_dictize.activity_list_dictize(
        activities, context,
        include_data=True)

def dataset_bulk_import_count(log_contents):
    complete = 0
    for log_item in log_contents:
        complete = complete + log_item['log_content'].count('package_create')
    return complete

def get_group_color(group_id):

    first_char = group_id[0]

    color = {
        '0': 'firebrick',
        '1': 'darkorange',
        '2': 'darkkhaki',
        '3': 'olivedrab',
        '4': 'teal',
        '5': 'royalblue',
        '6': 'slateblue',
        '7': 'purple',
        '8': 'mediumvioletred',
        '9': 'darkslategray',
        'a': 'saddlebrown',
        'b': 'green',
        'c': 'firebrick',
        'd': 'darkorange',
        'e': 'darkkhaki',
        'f': 'olivedrab',
        'g': 'teal',
        'h': 'royalblue',
        'i': 'slateblue',
        'j': 'purple',
        'k': 'mediumvioletred',
        'l': 'darkslategray',
        'm': 'saddlebrown',
        'n': 'green',
        'o': 'firebrick',
        'p': 'darkorange',
        'q': 'darkkhaki',
        'r': 'olivedrab',
        's': 'teal',
        't': 'royalblue',
        'u': 'slateblue',
        'v': 'purple',
        'w': 'mediumvioletred',
        'x': 'darkslategray',
        'y': 'saddlebrown',
        'z': 'green'
    }

    return first_char in color and color[first_char] or 'gray'

def get_site_statistics():
    stats = {}
    stats['dataset_count'] = logic.get_action('package_search')(
        {}, {"rows": 1,"include_private":True})['count']
    if config.get('scheming.group_schemas', '') != '':
        query = model.Session.query(model.Group) \
            .filter(model.Group.state == 'active') \
            .filter(model.Group.type != 'organization') \
            .filter(model.Group.type != 'group')
    
        resultproxy = model.Session.execute(query).fetchall()
        stats['group_count'] = len(resultproxy)
    else:
        stats['group_count'] = len(logic.get_action('group_list')({}, {}))

    stats['organization_count'] = len(
        logic.get_action('organization_list')({}, {}))
    return stats

def convert_string_todate(str_date, format):
    return dt.strptime(str_date, format)

def get_opend_playground_url():
    return config.get('thai_gdc.opend_playground_url')

def get_catalog_org_type():
    return config.get('thai_gdc.catalog_org_type')

def get_is_as_a_service():
    return config.get('thai_gdc.is_as_a_service')

def get_gdcatalog_status_show():
    return config.get('thai_gdc.gdcatalog_status_show')

def get_gdcatalog_portal_url():
    return config.get('thai_gdc.gdcatalog_portal_url')

def get_gdcatalog_apiregister_url():
    return config.get('thai_gdc.gdcatalog_apiregister_url')

def get_gdcatalog_version_update():
    gdcatalog_harvester_url = config.get('thai_gdc.gdcatalog_harvester_url')
    request_proxy = config.get('thai_gdc.proxy_request', None)
    if request_proxy:
        proxies = {
            'http': config.get('thai_gdc.proxy_url', None),
            'https': config.get('thai_gdc.proxy_url', None)
        }
    else:
        proxies = None

    state = 'connection error'
    gdcatalog_version = 'gdcatalog'
    local_version = 'local'
    try:
        with requests.Session() as s:
            s.verify = False
            url = gdcatalog_harvester_url+'/base/admin/thai-gdc-update.json'
            headers = {'Content-type': 'application/json', 'Authorization': ''}
            res = s.get(url, headers = headers, proxies=proxies)
            log.info(res.text)
            gdcatalog_version = json.loads(res.text)['version']
            local_version = get_extension_version('version')
        if gdcatalog_version != local_version:
            state = gdcatalog_version
        else:
            state = 'updated'
    except:
        return state
    
    return state

def get_gdcatalog_state(zone, package_id):
    state = []
    gdcatalog_status_show = get_gdcatalog_status_show()
    gdcatalog_harvester_url = config.get('thai_gdc.gdcatalog_harvester_url')
    site_url = config.get('ckan.site_url')
    request_proxy = config.get('thai_gdc.proxy_request', None)
    if request_proxy:
        proxies = {
            'http': config.get('thai_gdc.proxy_url', None),
            'https': config.get('thai_gdc.proxy_url', None)
        }
    else:
        proxies = None
    if gdcatalog_status_show == 'true':
        try:
            with requests.Session() as s:
                s.verify = False
                if zone == 'published':
                    url = gdcatalog_harvester_url+'/api/3/action/gdcatalog_published_state'
                elif zone == 'nonpublish':
                    url = gdcatalog_harvester_url+'/api/3/action/gdcatalog_nonpublish_state'
                myobj = {"site_url": site_url.split("//")[1].split("/")[0], "package": package_id}
                myobj['site_url'] = myobj['site_url'].encode('ascii','ignore')
                myobj['package'] = myobj['package'].encode('ascii','ignore')
                log.info(json.dumps(myobj))
                headers = {'Content-type': 'application/json', 'Authorization': ''}
                res = s.post(url, data = json.dumps(myobj), headers = headers, proxies=proxies)
                log.info(res.json())
                state = res.json()
        except:
            return state
    return state

def get_users_non_member():
    users = opend_model.get_users_non_member()
    return [d['id'] for d in users]

def get_users_deleted():
    query = model.Session.query(model.User.name)
    query = query.filter_by(state='deleted')
    users_list = []
    for user in query.all():
        users_list.append(user[0])
    return users_list

def get_extension_version(attr):
    dirname, filename = os.path.split(os.path.abspath(__file__))
    f = open(dirname+'/public/base/admin/thai-gdc-update.json',) 
    data = json.load(f)
    return data[attr]

def get_action(action_name, data_dict=None):
    '''Calls an action function from a template. Deprecated in CKAN 2.3.'''
    if data_dict is None:
        data_dict = {}
    return logic.get_action(action_name)({}, data_dict)

def get_organizations(all_fields=False, include_dataset_count=False, sort="name asc"):
    context = {'user': c.user}
    data_dict = {
        'all_fields': all_fields,
        'include_dataset_count': include_dataset_count,
        'sort': sort}
    return logic.get_action('organization_list')(context, data_dict)

def get_groups(all_fields=False, include_dataset_count=False, sort="name asc"):
    context = {'user': c.user}
    data_dict = {
        'all_fields': all_fields,
        'include_dataset_count': include_dataset_count,
        'sort': sort}
    return logic.get_action('group_list')(context, data_dict)

def get_resource_download(resource_id):
    return opend_model.get_resource_download(resource_id)

def get_stat_all_view():
    num = opend_model.get_all_view()
    return num

def get_last_update_tracking():
    last_update = opend_model.get_last_update_tracking()
    return last_update

def day_thai(t):
    month = [
        _('January'), _('February'), _('March'), _('April'),
        _('May'), _('June'), _('July'), _('August'),
        _('September'), _('October'), _('November'), _('December')
    ]

    raw = str(t)
    tmp = raw.split(' ')
    dte = tmp[0]

    tmp = dte.split('-')
    m_key = int(tmp[1]) - 1

    if h.lang() == 'th':
        dt = u"{} {} {}".format(int(tmp[2]), month[m_key], int(tmp[0]) + 543)
    else:
        dt = u"{} {}, {}".format(month[m_key], int(tmp[2]), int(tmp[0]))

    return dt

def facet_chart(type, limit):
    items = h.get_facet_items_dict(type, limit)
    i = 1
    data = []
    context = {'model': model}
    for item in items:
        my_dict = {column: value for column, value in item.items()}
        item['rownum'] = i
        if type == 'groups':
            group_dict = logic.get_action('group_show')(context, {'id': item['name']})
            item['image_url'] = group_dict['image_url']
        data.append(item)
        i += 1

    return data

def get_recent_view_for_package(package_id):
    rs = model.TrackingSummary.get_for_package(package_id)
    return rs['recent']

def get_featured_pages(per_page):
    pages = opend_model.get_featured_pages(per_page)
    return pages

def get_page(name):
    #if db.pages_table is None:
    #    db.init_db(model)
    page = opend_model.get_page(name)
    return page

def is_user_sysadmin(user=None):
    """Returns True if authenticated user is sysadmim
    :rtype: boolean
    """
    if user is None:
        user = toolkit.c.userobj
    return user is not None and user.sysadmin


def user_has_admin_access(include_editor_access=False):
    user = toolkit.c.userobj
    # If user is "None" - they are not logged in.
    if user is None:
        return False
    if is_user_sysadmin(user):
        return True

    groups_admin = user.get_groups('organization', 'admin')
    groups_editor = user.get_groups('organization', 'editor') if include_editor_access else []
    groups_list = groups_admin + groups_editor
    organisation_list = [g for g in groups_list if g.type == 'organization']
    return len(organisation_list) > 0

def get_all_groups():
    groups = toolkit.get_action('group_list')(
        data_dict={'include_dataset_count': False, 'all_fields': True})
    pkg_group_ids = set(group['id'] for group
                        in c.pkg_dict.get('groups', []))
    return [[group['id'], group['display_name']]
            for group in groups if
            group['id'] not in pkg_group_ids]

def get_all_groups_all_type(type=None):    
    user_groups = opend_model.get_groups_all_type(type)

    pkg_group_ids = set(group['id'] for group
                            in c.pkg_dict.get('groups', []))
    return [[group['id'], group['display_name']]
                            for group in user_groups if
                            group['id'] not in pkg_group_ids]

def users_in_organization(organization_id):
    ''' users in organization '''
    query = model.Session.query(model.Member) \
        .filter(model.Member.state == 'active') \
        .filter(model.Member.table_name == 'user') \
        .filter(model.Member.group_id == organization_id)
    users = query.all()
    context = {'model': model,
                    'user': c.user, 'auth_user_obj': c.userobj}
    users_list = []
    for user in users:
        users_list.append(model_dictize.member_dictize(user, context))
    return users_list

def get_suggest_view(resources):
    suggest_view_list = []
    for rs in resources:
        if rs.get('resource_private','') != "True":
            view_list = toolkit.get_action('resource_view_list')(data_dict={'id': rs['id']})

            for v in view_list:
                v_des = v['description'].strip()

                if len(v_des) > 0 and v_des[0] == '*':
                    suggest_view_list.append({
                        'title': v['title'],
                        'resource_id': v['resource_id'],
                        'view_id': v['id']
                    })

    return suggest_view_list


def get_conf_group(conf_group):
    try:
        conf = toolkit.get_action('gdc_agency_get_conf_group')(data_dict={'conf_group': conf_group})
        if 'EVENT_IMAGE' in conf.keys() and conf['EVENT_IMAGE'].strip() != '' \
                and not conf['EVENT_IMAGE'].startswith('http'):
            conf['EVENT_IMAGE'] = '/uploads/admin/{}'.format(conf['EVENT_IMAGE'])
        return conf
    except:
        return {}

def get_last_modified_datasets(limit):
    try:
        package = model.Package
        q = model.Session.query(package.name, package.title, package.type, package.metadata_modified.label('date_modified')).filter(package.state == 'active').filter(package.private == False).order_by(package.metadata_modified.desc()).limit(limit)
        packages = q.all()
    except:
        return []
    return packages

def get_popular_datasets(limit):
    package_list = []

    result_pkg_list = toolkit.get_action('package_search')(data_dict={'sort': 'views_total desc','rows':limit})
    for item in result_pkg_list['results']:
        tracking_summary = (model.TrackingSummary.get_for_package(item['id']))
        package_list.append({
            'name': item['name'],
            'title': item['title'],
            'type': item['type'],
            'date_modified' : item['metadata_modified'],
            'total_view': tracking_summary['total']})

    return package_list

def _link_to_customize(text, *args, **kwargs):
    '''Common link making code for several helper functions'''
    assert len(args) < 2, 'Too many unnamed arguments'

    def _link_class(kwargs):
        ''' creates classes for the link_to calls '''
        suppress_active_class = kwargs.pop('suppress_active_class', False)
        if not suppress_active_class and h._link_active(kwargs):
            active = ' active'
        else:
            active = ''
        kwargs.pop('highlight_actions', '')
        return kwargs.pop('class_', '') + active or None

    def _create_link_text(text, **kwargs):
        ''' Update link text to add a icon or span if specified in the
        kwargs '''
        if kwargs.pop('inner_span', None):
            text = h.literal('<span>') + text + h.literal('</span>')
        if icon:
            text = h.literal('<i class="fa fa-%s"></i> ' % icon) + text
        if img:
            text = h.literal('<div class="nav-link-content">') + h.literal('<img class="img-nav" src="%s"> ' % img) + h.literal('<p class="nav-text" >') + text + h.literal('</p>') + h.literal('</div>')
        return text

    icon = kwargs.pop('icon', None)
    img = kwargs.pop('img', None)
    cls = _link_class(kwargs)
    return h.link_to(
        _create_link_text(text, **kwargs),
        h.url_for(*args, **kwargs),
        cls=cls
    )


def _make_menu_item_customize(menu_item, title, **kw):
    ''' build a navigation item used for example breadcrumbs

    outputs <li><a href="..."></i> title</a></li>

    :param menu_item: the name of the defined menu item defined in
    config/routing as the named route of the same name
    :type menu_item: string
    :param title: text used for the link
    :type title: string
    :param **kw: additional keywords needed for creating url eg id=...

    :rtype: HTML literal

    This function is called by wrapper functions.
    '''
    check_route = kw.pop('check_route', None)
    if check_route : 
        menu_item = h.map_pylons_to_flask_route_name(menu_item)
        _menu_items = config['routes.named_routes']   

    # for page_def in PAGE_DEFINITIONS:
    #     _menu_items[page_def['name']] = {'function_type': page_def['function_type'],'controller': page_def['controller'], 'action': page_def['action'], 'needed': page_def['needed']}
    
        if menu_item not in _menu_items:
            raise Exception('menu item `%s` cannot be found' % menu_item)
    
        item = copy.copy(_menu_items[menu_item])
        item.update(kw)
        active = h._link_active(item)
        needed = item.pop('needed')
        for need in needed:
            if need not in kw:
                raise Exception('menu item `%s` need parameter `%s`'
                            % (menu_item, need))
        link = _link_to_customize(title, menu_item, suppress_active_class=True, **item)
        if active:
            return h.literal('<li class="active">') + link + h.literal('</li>')
        return h.literal('<li>') + link + h.literal('</li>')
    else:
        link = _link_to_customize(title, menu_item, suppress_active_class=True, **kw)
        return h.literal('<li>') + link + h.literal('</li>')
    

def build_nav_main_customize(*args):
    ''' build a set of menu items.

    args: tuples of (menu type, title) eg ('login', _('Login'))
    outputs <li><a href="...">title</a></li>
    '''
    output = ''
    for item in args:
        menu_item, title, img, check_route = item[:4]
        if len(item) == 5 and not check_access(item[4]):
            continue
        output += _make_menu_item_customize(menu_item, title, img=img, check_route=check_route)
    return output

def get_articles_news_list():
    state = []
    site_url = config.get('ckan.site_url')
    request_proxy = config.get('thai_gdc.proxy_request', None)
    proxies = None
    
    if request_proxy:
        proxies = {
            'http': config.get('thai_gdc.proxy_url', None),
            'https': config.get('thai_gdc.proxy_url', None)
        }
    
    try:
        with requests.Session() as s:
            s.verify = False
            url = site_url + '/api/3/action/ckanext_pages_list'
            headers = {'Content-type': 'application/json', 'Authorization': ''}
            res = s.get(url, headers=headers, proxies=proxies)
            
            # Check if the response status code is 200 (OK)
            # Use res.json() directly, as it returns the JSON-decoded content
            response_json = res.json()
            if "result" in response_json:
                state = response_json["result"]
            
    except requests.RequestException as e:
        print(e)
    
    return state
