# encoding: utf-8

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation, DefaultPermissionLabels
from ckanext.thaigdc_governance import helpers as gh
import ckan.model as model
from pylons import config
from ckan import logic
import ckan.authz as authz
from ckan.logic.auth.create import _check_group_auth
from six import string_types
import ckan.logic.auth as logic_auth
from ckanext.thaigdc_governance import blueprint
from ckan.common import _
import ckan.lib.navl.dictization_functions as df
from ckan.model.core import State
from ckanext.thaigdc_governance import cli
from collections import OrderedDict
import sys
from ckan.model import (PACKAGE_NAME_MIN_LENGTH)
import ckan.lib.helpers as h

from ckanext.thaigdc_governance.logic import (
    rebuild_packages, governance_send_mail, user_member_create, processing_update_state
)

import logging

log = logging.getLogger(__name__)
Invalid = df.Invalid
missing = df.missing

ROLE_PERMISSIONS = OrderedDict([
    ('admin', ['admin', 'membership']),
    ('owner', ['read', 'delete_dataset', 'create_dataset', 'update_dataset', 'manage_group']),
    ('member', ['read', 'manage_group']),
    ('editor', ['read', 'delete_dataset', 'create_dataset', 'update_dataset', 'manage_group', 'governance']),
])
authz.ROLE_PERMISSIONS = ROLE_PERMISSIONS

class ThaigdcGovernancePlugin(plugins.SingletonPlugin, DefaultTranslation, DefaultPermissionLabels):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IPermissionLabels)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IResourceController, inherit=True)

    # IBlueprint
    def get_blueprint(self):
        return blueprint.governance
    
    # IClick
    def get_commands(self):
        return cli.get_commands()

    def get_validators(self):
        return {
            'package_title_validator': package_title_validator,
            'package_name_validator': package_name_validator,
        }

    def get_dataset_labels(self, dataset_obj):
        try:
            extra = model.Session.query(model.PackageExtra).filter_by(package_id=dataset_obj.id).all()
            disclosure = ''
            for eitem in extra:
                if eitem.key == 'disclosure':
                    disclosure = eitem.value
            #view_users = json.loads(dataset_obj.extras.get('view_users', '[]'))
            labels = super(ThaigdcGovernancePlugin, self).get_dataset_labels(dataset_obj)
            steward_organization = model.Group.get(config.get('thaigdc_governance.steward_organization_name', 'data-steward-committee'))
            if steward_organization and dataset_obj.type == 'dataset':
                labels.append(u'view-alluser')
                if disclosure == u'secret' or dataset_obj.state == 'pending':
                    labels = [u'member-'+steward_organization.id]
                    labels.append(u'creator-'+dataset_obj.creator_user_id)
                    labels.append(u'owner-'+dataset_obj.owner_org)
            elif steward_organization and dataset_obj.type == 'prepare':
                #labels = [x for x in labels if not x.startswith('member') and not x.startswith('public') ]
                labels = [x for x in labels if not x.startswith('public') ]
                labels.append(u'creator-'+dataset_obj.creator_user_id)
                labels.append(u'member-'+steward_organization.id)
                labels.append(u'member-'+dataset_obj.owner_org)
            else:
                labels.append(u'member-'+steward_organization.id)
            
            if dataset_obj.type == 'processing' or dataset_obj.type == 'requestdata':
                labels = [u'member-'+steward_organization.id]
                labels.append(u'owner-'+dataset_obj.owner_org)

        except:
            return labels

        return labels #+ [u'view-alluser']

    def get_user_dataset_labels(self, user_obj):
        labels = super(ThaigdcGovernancePlugin, self).get_user_dataset_labels(user_obj)

        if user_obj:
            labels.append(u'view-alluser')
            for org in h.organizations_available(permission='governance'):
                labels.append(u'owner-'+org['id'])

        return labels

    def dataset_facets(self, facets_dict, package_type):

        facets_dict['data_type'] = toolkit._('Dataset Type') #ประเภทชุดข้อมูล
        facets_dict['data_category'] = toolkit._('Data Category') #หมวดหมู่ตามธรรมาภิบาลข้อมูล
        facets_dict['disclosure'] = toolkit._('Disclosure')
        return facets_dict

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_public_directory(config_, 'fanstatic')
        toolkit.add_resource('fanstatic', 'thaigdc_governance')

        config_['scheming.dataset_schemas'] = config_.get('scheming.dataset_schemas','ckanext.thaigdc_governance:ckan_dataset.json ckanext.thaigdc_governance:ckan_prepare.json ckanext.thaigdc_governance:ckan_processing.json ckanext.thaigdc_governance:ckan_requestdata.json')
        config_['thaigdc_governance.steward_organization_name'] = config_.get('thaigdc_governance.steward_organization_name', 'data-steward-committee')
        config_['thai_gdc.proxy_request'] = True
        config_['thai_gdc.proxy_url'] = 'http://proxy.mea.or.th:9090'
        
    def update_config_schema(self, schema):

        ignore_missing = toolkit.get_validator('ignore_missing')
        unicode_safe = toolkit.get_validator('unicode_safe')

        schema.update({
            'thaigdc_governance.admin_user': [ignore_missing, unicode_safe],
            'thaigdc_governance.steward_organization_name': [ignore_missing, unicode_safe],
            'thaigdc_governance.datasteward_groupmail': [ignore_missing, unicode_safe]
        })

        return schema
    
    def _isEnglish(self, s):
        try:
            s.encode(encoding='utf-8').decode('ascii')
        except UnicodeDecodeError:
            return False
        else:
            return True
    
    def before_search(self, search_params):
        fq = search_params.get('fq','')
        q = search_params.get('q','')

        try:
            if toolkit.c.action == 'action' and not 'disclosure:' in fq and not 'disclosure:' in q:
                fq = fq+' +(disclosure:public OR disclosure:registered)'
        except:
            fq = fq

        if not 'creator_user_id' in fq and not 'creator_user_id' in q:
            if not 'type:' in fq and not 'type:' in q:
                search_params['fq'] = fq+' +type:dataset'
        else:
            if not 'type:' in fq and not 'type:' in q:
                search_params['fq'] = fq+' +(type:prepare OR type:dataset)'
        
        search_params['include_private'] = True

        return search_params
    
    # IResourceController
    def before_show(self, res_dict):
        res_dict['resource_private'] = res_dict.get('resource_private','')
        del res_dict['resource_private']
        return res_dict
    
    # IAuthFunctions
    def get_auth_functions(self):
        auth_functions = {
            'package_update': self.package_update,
            'steward': self.steward,
            'resource_create': self.resource_create,
        }
        return auth_functions
    
    # IActionFunctions
    def get_actions(self):
        action_functions = {
            'rebuild_packages': rebuild_packages,
            'governance_send_mail': governance_send_mail,
            'user_member_create': user_member_create,
            'processing_update_state': processing_update_state,
        }
        return action_functions
    
    def resource_create(self, context, data_dict):
        model = context['model']
        user = context.get('user')

        package_id = data_dict.get('package_id')
        if not package_id and data_dict.get('id'):
            # This can happen when auth is deferred, eg from `resource_view_create`
            resource = logic_auth.get_resource_object(context, data_dict)
            package_id = resource.package_id

        if not package_id:
            raise logic.NotFound(
                _('No dataset id provided, cannot check auth.')
            )

        # check authentication against package
        pkg = model.Package.get(package_id)
        if not pkg:
            raise logic.NotFound(
                _('No package found for this resource, cannot check auth.')
            )

        pkg_dict = {'id': pkg.id}
        authorized = authz.is_authorized('package_update', context, pkg_dict).get('success')

        pkg_dict = logic.get_action("package_show")(context, {
                'id': pkg.id
            })

        if not authorized or pkg_dict.get('disclosure') in ['first_trusted','second_trusted','secret']:
            return {'success': False,
                    'msg': _('User %s not authorized to create resources on dataset %s') %
                            (str(user), package_id)}
        else:
            return {'success': True}
    
    def package_update(self, context, data_dict):
        model = context['model']
        user = context.get('user')

        package = logic_auth.get_package_object(context, data_dict)
        pkg_dict = logic.get_action("package_show")(context, {
                'id': package.id
            })
        user_obj = model.User.get(user)

        if package.type == 'prepare' and (pkg_dict.get('processing_dataset_id') == '' or pkg_dict.get('processing_dataset_id') == 'finished' or pkg_dict.get('processing_dataset_id') == None) and user_obj.id != pkg_dict.get('creator_user_id'):
            return {'success': False}
        if package.type == 'dataset' or (package.type == 'prepare' and pkg_dict.get('processing_dataset_id') and pkg_dict.get('processing_dataset_id') != ''):
            return self.steward(context, data_dict)#{'success': False}
        if package.owner_org:
            # if there is an owner org then we must have update_dataset
            # permission for that organization
            check1 = authz.has_user_permission_for_group_or_org(
                package.owner_org, user, 'update_dataset'
            )
        else:
            # If dataset is not owned then we can edit if config permissions allow
            if authz.auth_is_anon_user(context):
                check1 = all(authz.check_config_permission(p) for p in (
                    'anon_create_dataset',
                    'create_dataset_if_not_in_organization',
                    'create_unowned_dataset',
                    ))
            else:
                check1 = all(authz.check_config_permission(p) for p in (
                    'create_dataset_if_not_in_organization',
                    'create_unowned_dataset',
                    )) or authz.has_user_permission_for_some_org(
                    user, 'create_dataset')

        if not check1:
            success = False
            if authz.check_config_permission('allow_dataset_collaborators'):
                # if org-level auth failed, check dataset-level auth
                # (ie if user is a collaborator)
                user_obj = model.User.get(user)
                if user_obj:
                    success = authz.user_is_collaborator_on_dataset(
                        user_obj.id, package.id, ['admin', 'editor'])
            if not success:
                return {'success': False,
                        'msg': _('User %s not authorized to edit package %s') %
                                (str(user), package.id)}
        else:
            check2 = _check_group_auth(context, data_dict)
            if not check2:
                return {'success': False,
                        'msg': _('User %s not authorized to edit these groups') %
                                (str(user))}
        
        return {'success': True}
    
    def steward(self, context, data_dict):
        user = context['user']
        steward_organization = config.get('thaigdc_governance.steward_organization_name', 'data-steward-committee')
        authorized = authz.has_user_permission_for_group_or_org(steward_organization,
                                                                user,
                                                                'create_dataset')
        if authorized:
            return {'success': True}

        if len(h.organizations_available(permission='governance')):
            return {'success': True}

        return {'success': False, 'msg': _('User {0} not authorized'.format(user))}

    def create(self, package):
        self.modify_package_before(package)
        if package.type == 'dataset':
            package.type = 'prepare'
    
    def edit(self, package):
        self.modify_package_before(package)
    
    def modify_package_before(self, package):
        package.state = 'active'

        for extra in package.extras_list:
            if extra.key == 'objective' and isinstance(extra.value, string_types):
                extra.value = self.unicode_string_convert(extra.value)
            elif extra.key == 'disclosure':
                if extra.value == u'public':
                    package.private = False
                else:
                    package.private = True
    
    def unicode_string_convert(self, value):
        values = value.strip('[]').split(',')
        value_list = ""
        for v in values:
            try:
                value_list = value_list + v.strip(' ').encode('latin-1').decode('unicode-escape')
            except:
                value_list = value_list + v
        return "["+value_list.replace('""','","')+"]"
    
    def get_helpers(self):
        return {
            'thaigdc_governance_get_processing_governance_state': gh.get_processing_governance_state,
            'thaigdc_governance_get_activity_data':gh.get_activity_data,
            'get_site_statistics':gh.get_site_statistics,
            'thaigdc_governance_get_action_foradmin':gh.get_action_foradmin,
            'thaigdc_governance_day_thai':gh.day_thai,
            'thaigdc_governance_check_package_owner': gh.check_package_owner,
            'thaigdc_governance_get_user': gh.get_user,
        }

def package_name_validator(key, data, errors, context):
    model = context['model']
    session = context['session']
    package = context.get('package')

    query = session.query(model.Package.state).filter_by(name=data[key])
    if package:
        package_id = package.id
    else:
        package_id = data.get(key[:-1] + ('id',))
    if package_id and package_id is not missing:
        query = query.filter(model.Package.id != package_id)
    result = query.first()
    if result and result.state != State.DELETED:
        errors[key].append(_('That URL is already in use.'))
    elif result and result.state == State.DELETED:
        errors[key].append(_('That URL is already in trash.'))

    value = data[key]
    if len(value) < PACKAGE_NAME_MIN_LENGTH:
        raise Invalid(
            _('Name "%s" length is less than minimum %s') % (value, PACKAGE_NAME_MIN_LENGTH)
        )
    if len(value) > 70:
        raise Invalid(
            _('Name "%s" length is more than maximum %s') % (value, 70)
        )
    if data.get(key[:-1] + ('type',)) == 'prepare' and data.get(key[:-1] + ('publish_dataset_id',)) is missing and value.startswith(tuple(['gprepare-','gprocessing-','garchive-'])):
        raise Invalid(
            _('That name cannot be used')
        )

def package_title_validator(key, data, errors, context):
    model = context['model']
    session = context['session']
    package = context.get('package')

    query = session.query(model.Package.state).filter_by(title=data[key]).filter(model.Package.type=='prepare')
    if package:
        package_id = package.id
    else:
        package_id = data.get(key[:-1] + ('id',))
    if package_id and package_id is not missing:
        query = query.filter(model.Package.id != package_id)
    result = query.first()
    if result and result.state != State.DELETED and data.get(key[:-1] + ('type',)) == 'prepare':
        raise Invalid(
            _('That title is already in use.')
        )

    query = session.query(model.Package.state).filter_by(title=data[key]).filter(model.Package.type=='dataset')
    if data.get(key[:-1] + ('name',)).startswith('gprepare-') and data.get(key[:-1] + ('publish_dataset_id',)) is not missing:
        query = query.filter(model.Package.id != data.get(key[:-1] + ('publish_dataset_id',)))
    result = query.first()
    if result and result.state != State.DELETED and data.get(key[:-1] + ('type',)) == 'prepare':
        raise Invalid(
            _('That title is already in use.')
        )

def _trans_role_admin():
    return _('Admin')

def _trans_role_editor():
    return _('Editor')

def _trans_role_member():
    return _('Member')

def _trans_role_owner():
    return _('Owner')

def trans_role(role):
    module = sys.modules[__name__]
    return getattr(module, '_trans_role_%s' % role)()

authz.trans_role = trans_role
