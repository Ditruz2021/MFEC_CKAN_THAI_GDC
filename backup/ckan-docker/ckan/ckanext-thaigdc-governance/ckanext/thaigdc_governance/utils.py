# encoding: utf-8

import ckan.plugins.toolkit as toolkit
import ckan.model as model
import uuid
from ckan.common import config
import ckan.plugins as plugins
import datetime
import six
import logging

log = logging.getLogger(__name__)

def steward_organization_create():
    admin_user = config.get('thaigdc_governance.admin_user')
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }
    toolkit.get_action('organization_create')(context, {"name":"data-steward-committee", "title":"คณะกรรมการธรรมาภิบาลข้อมูล/ทีมบริกรข้อมูล"})

def _create_archive(package_id):
    admin_user = config.get('thaigdc_governance.admin_user')
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }
    pkg_dict = plugins.toolkit.get_action('package_show')(context, {'id':package_id}) #get dataset
    pkg_dict_original = pkg_dict.copy()
    dt = datetime.datetime.now()
    
    pkg_dict['type'] = 'processing'
    pkg_dict['previous_governance_state'] = 'approval'
    pkg_dict['governance_state'] = 'complete'
    if str(pkg_dict['private']) == "True":
        pkg_dict['governance_disclosure'] = 'registered'
    else:
        pkg_dict['governance_disclosure'] = 'public'
    pkg_dict['governance_data_category'] = pkg_dict['data_category']
    pkg_dict['governance_allow_harvest'] = pkg_dict['allow_harvest']
    pkg_dict['governance_notes'] = u'สร้างเริ่มต้นโดยระบบ'
    pkg_dict['governance_steward'] = str(context['auth_user_obj'].id)
    pkg_dict['governance_date'] = dt.strftime("%Y-%m-%d")
    
    pkg_dict['prepare_dataset_id'] = package_id
    pkg_dict['name'] = 'garchive-'+dt.strftime("%Y%m%d%H%M%S")+'-'+pkg_dict['name']
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

def migrate_datasets():
    admin_user = config.get('thaigdc_governance.admin_user')
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }
    packages = model.Session.query(model.Package).all()
    from ckan.lib.search import rebuild
    for package in packages:
        if package.type in ('prepare','processing','requestdata'):
            plugins.toolkit.get_action('package_delete')(context, {'id':package.id}) #delete
            #plugins.toolkit.get_action('dataset_purge')(context, {'id':package.id}) #purge
        elif package.type == 'dataset':
            model.Session.query(model.PackageExtra).filter(model.PackageExtra.package_id == package.id).filter(model.PackageExtra.key == 'disclosure').delete()
            if str(package.private) == "True":
                pkg_extra = model.PackageExtra(id=str(uuid.uuid4()),
                                key='disclosure',
                                value='registered',
                                state='active',
                                package_id=package.id)
                model.Session.add(pkg_extra)
                model.Session.commit()
            else:
                pkg_extra = model.PackageExtra(id=str(uuid.uuid4()),
                                key='disclosure',
                                value='public',
                                state='active',
                                package_id=package.id)
                model.Session.add(pkg_extra)
                model.Session.commit()
            rebuild(package.id)
            _create_archive(package.id)

def clear_all():
    admin_user = config.get('thaigdc_governance.admin_user')
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': admin_user,
        u'for_view': True,
        u'auth_user_obj': model.User.by_name(admin_user)
    }
    packages = model.Session.query(model.Package).all()
    from ckan.lib.search import rebuild
    for package in packages:
        if package.type in ('prepare','processing','requestdata'):
            plugins.toolkit.get_action('package_delete')(context, {'id':package.id}) #delete
            #plugins.toolkit.get_action('dataset_purge')(context, {'id':package.id}) #purge
        elif package.type == 'dataset':
            model.Session.query(model.PackageExtra).filter(model.PackageExtra.package_id == package.id).filter(model.PackageExtra.key == 'disclosure').delete()
            model.Session.query(model.Package).filter_by(id=package.id).update({u'state': 'active'})
            model.Session.commit()
            rebuild(package.id)

    model.Session.query(model.Member).filter(model.Member.table_name == 'user').filter(model.Member.capacity == 'owner').delete()
    model.Session.commit()
    plugins.toolkit.get_action('organization_delete')(context, {'id':'data-steward-committee'}) #delete
    #plugins.toolkit.get_action('organization_purge')(context, {'id':'data-steward-committee'}) #purge
