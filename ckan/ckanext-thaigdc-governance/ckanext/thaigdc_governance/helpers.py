# encoding: utf-8

import ckan.model as model
import logging
from pylons import config
import ckan.logic as logic
from ckan.common import g, _,request, asbool
import ckan.lib.helpers as h
from datetime import timedelta
import requests
import json

log = logging.getLogger(__name__)

def check_package_owner(package_id):
    pakcgae_obj = model.Package.get(package_id)
    user_obj = model.User.get(pakcgae_obj.creator_user_id)
    current_user_obj = model.User.get(g.user)
    return user_obj == current_user_obj

def get_action_foradmin(action_name, data_dict=None):

    admin_user = config.get('thaigdc_governance.admin_user','ckan-admin')
    
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }

    if data_dict is None:
        data_dict = {}
    return logic.get_action(action_name)(context, data_dict)

def get_site_statistics():
    stats = {}
    stats['dataset_count'] = logic.get_action('package_search')(
        {}, {"rows": 1,"include_private":True,"fq":"dataset_type:dataset"})['count']
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

def get_activity_data(activity_id):
    activity_data = {}
    try:
        q = model.Session.query(model.Activity).filter(model.Activity.id == activity_id)
        activity_data = q.first().data
    except:
        return activity_data
    return activity_data

def get_processing_governance_state(processing_dataset_id):
    governance_state = ''
    try:
        q = model.Session.query(model.PackageExtra).filter(model.PackageExtra.package_id == processing_dataset_id).filter(model.PackageExtra.key == 'governance_state').filter(model.PackageExtra.state == 'active')
        governance_state = q.first().value
    except:
        return governance_state
    return governance_state

def day_thai(t):
    month = [
        _('January'), _('February'), _('March'), _('April'),
        _('May'), _('June'), _('July'), _('August'),
        _('September'), _('October'), _('November'), _('December')
    ]

    raw = str(t + timedelta(hours=7))
    tmp = raw.split(' ')
    dte = tmp[0]
    dte_time = tmp[1].split(':')[0] + '.' + tmp[1].split(':')[1] + u' น.'

    tmp = dte.split('-')
    m_key = int(tmp[1]) - 1

    if h.lang() == 'th':
        dt = u"{} {} {} {}".format(int(tmp[2]), month[m_key], int(tmp[0]) + 543, dte_time)
    else:
        dt = u"{} {}, {}".format(month[m_key], int(tmp[2]), int(tmp[0]))

    return dt

def get_user(user):
    if not isinstance(user, model.User):
        user = model.User.get(user)
        if user:
            return user
    return user

def get_request_dataset_list(id = ''):
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
            url = site_url + '/api/3/action/package_request_list'
            headers = {'Content-type': 'application/json', 'Authorization': g.userobj.apikey}
            if id:
                params = {'id': id}
            else:
                params = {}
            res = s.get(url,data=json.dumps(params),headers=headers, proxies=proxies)
            
            # Check if the response status code is 200 (OK)
            # Use res.json() directly, as it returns the JSON-decoded content
            response_json = res.json()
            if "result" in response_json:
                state = response_json["result"]
            
    except requests.RequestException as e:
        print(e)
    
    return state
def send_request_dataset(id = ''):
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
            url = site_url + '/api/3/action/package_request_update'
            headers = {'Content-type': 'application/json', 'Authorization': g.userobj.apikey}
            if id:
                params = {'id': id}
            else:
                params = {}
            res = s.post(url,data=json.dumps(params),headers=headers, proxies=proxies)
            
            # Check if the response status code is 200 (OK)
            # Use res.json() directly, as it returns the JSON-decoded content
            response_json = res.json()
            if "result" in response_json:
                state = response_json["result"]
            
    except requests.RequestException as e:
        print(e)
    
    return state