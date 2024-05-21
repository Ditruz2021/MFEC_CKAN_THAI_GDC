# encoding: utf-8

import ckan.logic as logic
import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from pylons import config
import ckan.model as model
import re
from ckan.plugins.toolkit import (
    _, c, h
    )
from ckanapi import LocalCKAN
import six
import datetime
import os

_check_access = logic.check_access
_get_or_bust = logic.get_or_bust
NotFound = logic.NotFound
ValidationError = logic.ValidationError

log = logging.getLogger(__name__)

def _username_format(username):
    username = username.strip()
    username = username.replace('@', '-at-')
    username = username.replace('.', '_')
    username = username.replace(' ', '_')
    username = username.replace(',', '-')
    username = "".join(re.split("[^a-zA-Z0-9-_]*", username))
    username = username.lower()
    return username

def user_member_create(context, data_dict):
    _check_access('sysadmin', context, data_dict)
    dd_name = _get_or_bust(data_dict, 'name')
    dd_password = _get_or_bust(data_dict, 'password')
    dd_email = _get_or_bust(data_dict, 'email')
    dd_org_id = _get_or_bust(data_dict, 'org_id')
    if 'role' in data_dict:
        dd_role = data_dict['role']
    else:
        dd_role = 'editor'
    user_member = ''

    dd_name = _username_format(dd_name)

    if len(dd_password) < 8:
        raise ValidationError

    organization = model.Group.get(dd_org_id)
    if not organization:
        raise NotFound

    existing_user = plugins.toolkit.get_action('user_list')(None, {'email':dd_email})
    if len(existing_user) == 0:
        user_dict = {'name':dd_name, 'password':dd_password, 'fullname':data_dict['fullname'], 'email':dd_email}
        user = plugins.toolkit.get_action('user_create')(None, user_dict)
        user_apikey = plugins.toolkit.get_action('user_generate_apikey')(None, {"id":user['id']})
        user_member = plugins.toolkit.get_action('organization_member_create')(None, {"id":dd_org_id, "username":dd_name, "role":dd_role})
        user_member['apikey'] = user_apikey['apikey']
    else:
        user = plugins.toolkit.get_action('user_show')(None, {'id':dd_name})
        existing_member = plugins.toolkit.get_action('organization_list_for_user')(None, {'id':dd_name})
        if len(existing_member) > 0:
            found_in_org = 0
            for emb in existing_member:
                if emb['id'] == dd_org_id:
                    found_in_org = 1
                else:
                    plugins.toolkit.get_action('organization_member_delete')(None, {'id':emb['id'],'username':dd_name})
        if found_in_org == 0:
            user_member = plugins.toolkit.get_action('organization_member_create')(None, {"id":dd_org_id, "username":dd_name, "role":"editor"})
        else:
            user_member = existing_user
        user_member['apikey'] = user['apikey']
    user_member['user_id'] = user_member['table_id']
    del user_member['table_id']
    
    return user_member

def _create_email_body(event, body_dict):
    site_url = config.get('ckan.site_url')

    body = u''
    if event == 'owner_submit_forowner':
        body += u'ชุดข้อมูล: '+body_dict['package_title']+ u'\n'
        body += u'สถานะ: อยู่ระหว่างการพิจารณา\n'
        body += u'สามารถตรวจสอบสถานะชุดข้อมูลได้ที่: '+site_url+u'/dashboard/datasets (กรุณา login ที่ระบบก่อน)\n\n'
        body += u'คณะทำงานธรรมาภิบาลข้อมูล\n\n'
        body += u'หมายเหตุ: e-mail นี้ถูกส่งจากระบบแบบอัตโนมัติ กรุณาอย่าตอบกลับ (reply)'
    elif event == 'owner_submit_forsteward':
        body += u'เรียน คณะทำงานธรรมาภิบาลข้อมูล\nได้มีการดำเนินการ เพิ่มเติม/แก้ไข ชุดข้อมูลในระบบบัญชีข้อมูล (Data Catalog) รายละเอียดดังนี้\n'
        body += u'ผู้กรอกข้อมูล/ผู้ขออนุมัติ: '+body_dict['user_fullname']+u'\n'
        body += u'ชุดข้อมูล: '+body_dict['package_title']+u'\n'
        body += u'หน่วยงาน: '+body_dict['organization_title']+u'\n'
        body += u'การดำเนินการในระบบ: มีชุดข้อมูลรอการตรวจสอบ\n'
        body += u'ขอให้ท่านที่ได้รับมอบหมายในการกำกับดูแลข้อมูล ดำเนินการส่วนที่เกี่ยวข้อง ได้ที่: '+site_url+u'/governance/processing_state_wait (กรุณา login ที่ระบบก่อน)\n\n'
        body += u'หมายเหตุ: e-mail นี้ถูกส่งจากระบบแบบอัตโนมัติ กรุณาอย่าตอบกลับ (reply)'
    elif event == 'notify_approval_forsteward':
        body += u'เรียน คณะทำงานธรรมาภิบาลข้อมูล\nได้มีการดำเนินการ เพิ่มเติม/แก้ไข ชุดข้อมูลในระบบบัญชีข้อมูล (Data Catalog) รายละเอียดดังนี้\n'
        body += u'ผู้กรอกข้อมูล/ผู้ขออนุมัติ: '+body_dict['user_fullname']+u'\n'
        body += u'ชุดข้อมูล: '+body_dict['package_title']+u'\n'
        body += u'หน่วยงาน: '+body_dict['organization_title']+u'\n'
        body += u'การดำเนินการในระบบ: มีชุดข้อมูลรอการอนุมัติ\n'
        body += u'ขอให้ท่านที่ได้รับมอบหมายในการกำกับดูแลข้อมูล ดำเนินการส่วนที่เกี่ยวข้อง ได้ที่: '+site_url+u'/governance/processing_state_approval (กรุณา login ที่ระบบก่อน)\n\n'
        body += u'หมายเหตุ: e-mail นี้ถูกส่งจากระบบแบบอัตโนมัติ กรุณาอย่าตอบกลับ (reply)'
    elif event == 'notify_complete_forowner':
        body += u'ชุดข้อมูล: '+body_dict['package_title']+u'\n'
        body += u'สถานะ: ได้รับการอนุมัติให้เผยแพร่\n'
        body += u'หมวดหมู่ข้อมูลตามธรรมาภิบาลข้อมูลภาครัฐ: '+body_dict['data_category']+u'\n'
        body += u'ระดับชั้นข้อมูล: '+_(body_dict['disclosure'])+'\n'
        body += u'สามารถตรวจสอบสถานะชุดข้อมูลได้ที่: '+site_url+'/dataset/'+body_dict['package_name']+u' (กรุณา login ที่ระบบก่อน)\n\n'
        body += u'คณะทำงานธรรมาภิบาลข้อมูล\n\n'
        body += u'หมายเหตุ: e-mail นี้ถูกส่งจากระบบแบบอัตโนมัติ กรุณาอย่าตอบกลับ (reply)'
    elif event == 'notify_reject_forowner':
        body += u'ชุดข้อมูล: '+body_dict['package_title']+u'\n'
        body += u'สถานะ: ไม่ได้รับการอนุมัติให้เผยแพร่\n'
        body += u'เหตุผล/ข้อเสนอแนะ: '+body_dict['governance_notes']+'\n'
        body += u'สามารถตรวจสอบสถานะชุดข้อมูลได้ที่: '+site_url+u'/dashboard?q=reject (กรุณา login ที่ระบบก่อน)\n\n'
        body += u'คณะทำงานธรรมาภิบาลข้อมูล\n\n'
        body += u'หมายเหตุ: e-mail นี้ถูกส่งจากระบบแบบอัตโนมัติ กรุณาอย่าตอบกลับ (reply)'
    elif event == "requestdata_forrequester":
        body += u'รายการคำขอใช้ชุดข้อมูล: '+body_dict['package_title']+u'\n'
        body += u'สถานะ: อยู่ระหว่างการพิจารณา\n'
        body += u'สามารถตรวจสอบสถานะคำขอใช้ข้อมูลได้ที่: '+site_url+u'/dashboard/requestdatas (กรุณา login ที่ระบบก่อน)\n\n'
        body += u'คณะทำงานธรรมาภิบาลข้อมูล\n\n'
        body += u'หมายเหตุ: e-mail นี้ถูกส่งจากระบบแบบอัตโนมัติ กรุณาอย่าตอบกลับ (reply)'
    elif event == "requestdata_forsteward":
        body += u'เรียน คณะทำงานธรรมาภิบาลข้อมูล\nได้มีการดำเนินการ ขออนุมัติการใช้ข้อมูลในระบบบัญชีข้อมูล (Data Catalog) รายละเอียดดังนี้\n'
        body += u'ผู้กรอกข้อมูล/ผู้ขออนุมัติ: '+body_dict['requester_fullname']+u'\n'
        body += u'รายการคำขอใช้ชุดข้อมูล: '+body_dict['package_title']+u'\n'
        body += u'หน่วยงาน: '+body_dict['organization_title']+u'\n'
        body += u'การดำเนินการในระบบ: มีคำขอใช้ข้อมูลรอการตรวจสอบ\n'
        body += u'ขอให้ท่านที่ได้รับมอบหมายในการกำกับดูแลข้อมูล ดำเนินการส่วนที่เกี่ยวข้อง ได้ที่: '+site_url+u'/governance/requestdata/processing_state_wait_steward (กรุณา login ที่ระบบก่อน)\n\n'
        body += u'หมายเหตุ: e-mail นี้ถูกส่งจากระบบแบบอัตโนมัติ กรุณาอย่าตอบกลับ (reply)'
    elif event == "notify_requestdata_approval_forrequester":
        body += u'รายการคำขอใช้ชุดข้อมูล: '+body_dict['package_title']+u'\n'
        body += u'สถานะ: อนุมัติคำขอใช้ข้อมูล และอยู่ระหว่างแจ้งผู้ดูแลข้อมูล\n'
        body += u'สามารถตรวจสอบสถานะคำขอใช้ข้อมูลได้ที่: '+site_url+u'/dashboard/requestdatas'+'\n\n'
        body += u'คณะทำงานธรรมาภิบาลข้อมูล\n\n'
        body += u'หมายเหตุ: e-mail นี้ถูกส่งจากระบบแบบอัตโนมัติ กรุณาอย่าตอบกลับ (reply)'
    elif event == "notify_requestdata_approval_forsteward":
        body += u'เรียน คณะทำงานธรรมาภิบาลข้อมูล\nได้มีการดำเนินการ ขออนุมัติการใช้ข้อมูลในระบบบัญชีข้อมูล (Data Catalog) รายละเอียดดังนี้\n'
        body += u'ผู้กรอกข้อมูล/ผู้ขออนุมัติ: '+body_dict['requester_fullname']+u'\n'
        body += u'รายการคำขอใช้ชุดข้อมูล: '+body_dict['package_title']+u'\n'
        body += u'หน่วยงาน: '+body_dict['organization_title']+u'\n'
        body += u'การดำเนินการในระบบ: มีคำขอใช้ข้อมูลรอแจ้งผู้ดูแลข้อมูล\n'
        body += u'ขอให้ท่านที่ได้รับมอบหมายในการกำกับดูแลข้อมูล ดำเนินการส่วนที่เกี่ยวข้อง ได้ที่: '+site_url+u'/governance/requestdata/receive_state_wait_maintainer_notify (กรุณา login ที่ระบบก่อน)\n\n'
        body += u'หมายเหตุ: e-mail นี้ถูกส่งจากระบบแบบอัตโนมัติ กรุณาอย่าตอบกลับ (reply)'
    elif event == "notify_requestdata_approval_forowner":
        body += u'ชุดข้อมูล: '+body_dict['package_title']+' ('+site_url+'/dataset/'+body_dict['package_name']+u')\n'
        body += u'ผู้ขอใช้ข้อมูล: '+body_dict['requester_fullname']+u'\n'
        body += u'อีเมลผู้ขอใช้ข้อมูล: '+body_dict['requester_email']+u'\n'
        body += u'สามารถตรวจสอบรายการคำขอใช้ข้อมูลได้ที่: '+site_url+u'/dashboard/requested_packages (กรุณา login ที่ระบบก่อน)\n\n'
        body += u'คณะทำงานธรรมาภิบาลข้อมูล\n\n'
        body += u'หมายเหตุ: e-mail นี้ถูกส่งจากระบบแบบอัตโนมัติ กรุณาอย่าตอบกลับ (reply)'
    elif event == "notify_requestdata_reject_forrequester":
        body += u'รายการคำขอใช้ชุดข้อมูล: '+body_dict['package_title']+u'\n'
        body += u'สถานะ: ไม่ได้รับการอนุมัติให้ใช้ข้อมูล\n'
        body += u'เหตุผล: '+body_dict['summary_comment']+u'\n'
        body += u'สามารถตรวจสอบสถานะคำขอใช้ข้อมูลได้ที่: '+site_url+u'/dashboard/requestdatas (กรุณา login ที่ระบบก่อน)\n\n'
        body += u'คณะทำงานธรรมาภิบาลข้อมูล\n\n'
        body += u'หมายเหตุ: e-mail นี้ถูกส่งจากระบบแบบอัตโนมัติ กรุณาอย่าตอบกลับ (reply)'
    
    return body

def governance_send_mail(context, data_dict):
    _check_access('sysadmin', context, data_dict)
    user_id = _get_or_bust(data_dict, 'user_id')
    package_id = _get_or_bust(data_dict, 'package_id')
    event = _get_or_bust(data_dict, 'event')
    user_dict = toolkit.get_action('user_show')(context, {'id':user_id})
    pkg_dict = toolkit.get_action('package_show')(context, {'id':package_id})
    owner_org_dict = toolkit.get_action('organization_show')(context, {'id':pkg_dict['owner_org'],'include_users':'true'})

    dataowner_mail_list = []
    for user in owner_org_dict['users']:
        if user['capacity'] == 'owner':
            owner_dict = model.User.by_name(user['name'])
            dataowner_mail_list.append(owner_dict.email)

    datasteward_groupmail = config.get('thaigdc_governance.datasteward_groupmail','')
    body_dict = {}
    if event == 'owner_submit_forowner':
        subject = "[DataGov][Owner] ระบบได้รับคำขอพิจารณาชุดข้อมูลของท่าน"
        body_dict = {"package_title":pkg_dict['title']}
        body = _create_email_body(event, body_dict)
    elif event == 'owner_submit_forsteward':
        subject = "[DataGov][Steward] มีชุดข้อมูลรอการตรวจสอบ"
        body_dict = {"package_title":pkg_dict['title'], "user_fullname":user_dict['display_name'], "organization_title":pkg_dict['organization']['title']}
        body = _create_email_body(event, body_dict)
    elif event == 'notify_approval_forsteward':
        subject = "[DataGov][Steward] มีชุดข้อมูลรอการอนุมัติ"
        body_dict = {"package_title":pkg_dict['title'], "user_fullname":user_dict['display_name'], "organization_title":pkg_dict['organization']['title']}
        body = _create_email_body(event, body_dict)
    elif event == 'notify_complete_forowner':
        subject = "[DataGov][Owner] ชุดข้อมูลของท่านได้รับการอนุมัติให้เผยแพร่"
        body_dict = {"package_title":pkg_dict['title'],"package_name":pkg_dict['name'],"data_category":data_dict['data_category'],"disclosure":data_dict['disclosure']}
        body = _create_email_body(event, body_dict)
    elif event == 'notify_reject_forowner':
        subject = "[DataGov][Owner] ชุดข้อมูลของท่านไม่ได้รับการอนุมัติให้เผยแพร่"
        body_dict = {"package_title":pkg_dict['title'],"governance_notes":data_dict['governance_notes']}
        body = _create_email_body(event, body_dict)
    elif event == 'requestdata_forrequester':
        subject = "[DataGov][Requester] ระบบได้รับคำขอใช้ข้อมูลของท่าน"
        body_dict = {"package_title":pkg_dict['title']}
        body = _create_email_body(event, body_dict)
    elif event == 'requestdata_forsteward':
        req_dict = toolkit.get_action('package_show')(context, {'id':data_dict['request_id']})
        user_dict = toolkit.get_action('user_show')(context, {'id':req_dict['requester_id']})
        subject = "[DataGov][Steward] มีคำขอใช้ข้อมูลรอการตรวจสอบ"
        body_dict = {"package_title":pkg_dict['title'], "organization_title":pkg_dict['organization']['title'], "requester_fullname":user_dict['display_name']}
        body = _create_email_body(event, body_dict)
    elif event == 'notify_requestdata_approval_forrequester':
        subject = "[DataGov][Requester] คำขอใช้ข้อมูลของท่านได้รับการอนุมัติ"
        body_dict = {"package_title":pkg_dict['title']}
        body = _create_email_body(event, body_dict)
    elif event == 'notify_requestdata_approval_forsteward':
        req_dict = toolkit.get_action('package_show')(context, {'id':data_dict['request_id']})
        subject = "[DataGov][Steward] มีคำขอใช้ข้อมูลรอแจ้งผู้ดูแลข้อมูล"
        body_dict = {"package_title":pkg_dict['title'], "organization_title":pkg_dict['organization']['title'], "requester_fullname":user_dict['display_name']}
        body = _create_email_body(event, body_dict)
    elif event == 'notify_requestdata_approval_forowner':
        subject = "[DataGov][Owner] มีผู้ขอใช้ข้อมูลของท่าน และได้รับอนุมัติให้ใช้งาน"
        body_dict = {"package_title":pkg_dict['title'],"package_name":pkg_dict['name'],"requester_fullname":user_dict['display_name'],"requester_email":user_dict['email']}
        body = _create_email_body(event, body_dict)
    elif event == 'notify_requestdata_reject_forrequester':
        subject = "[DataGov][Requester] คำขอใช้ข้อมูลของท่านไม่ได้รับการอนุมัติ"
        body_dict = {"package_title":pkg_dict['title'],"summary_comment":data_dict['summary_comment']}
        body = _create_email_body(event, body_dict)

    try:
        if event == 'owner_submit_forowner' or event == 'notify_complete_forowner' or event == 'notify_reject_forowner':
            log.info('send_mail '+event)
            toolkit.mail_recipient('System Admin', user_dict['email'], subject, body)
        elif event == 'owner_submit_forsteward' or event == 'notify_approval_forsteward' or event == "requestdata_forsteward" or event == "notify_requestdata_approval_forsteward":
            log.info('send_mail '+event)
            for dataowner_mail in dataowner_mail_list:
                toolkit.mail_recipient('System Admin', dataowner_mail, subject, body)
            if datasteward_groupmail != '':
                toolkit.mail_recipient('System Admin', datasteward_groupmail, subject, body)
        elif event == "requestdata_forrequester" or event == "notify_requestdata_approval_forrequester" or event == "notify_requestdata_reject_forrequester":
            log.info('send_mail '+event)
            toolkit.mail_recipient('System Admin', user_dict['email'], subject, body)
        elif event == "notify_requestdata_approval_forowner":
            log.info('send_mail '+event)
            toolkit.mail_recipient('System Admin', pkg_dict['maintainer_email'] , subject, body)
    except:
        return "False"
    
    return "True"

def rebuild_packages(context, data_dict):
    _check_access('sysadmin', context, data_dict)
    from ckan.lib.search import rebuild
    [rebuild(package_id) for package_id in data_dict['datasets']]

def _create_dataset(context, data_dict):
    _check_access('package_create', context, data_dict)
    pkg_dict_create = ""
    package_id = _get_or_bust(data_dict, 'id')
    try:
        pkg_dict = plugins.toolkit.get_action('package_show')(None, {'id':package_id}) #get processing
        pkg_dict_prepare = plugins.toolkit.get_action('package_show')(None, {'id':pkg_dict['prepare_dataset_id']}) #get prepare

        user_obj = model.User.get(six.ensure_text(pkg_dict['creator_user_id']))
        context = {'model': model, 'session': model.Session, 'ignore_auth': True,
               'user': user_obj.name, 'auth_user_obj': None}
        if pkg_dict['governance_disclosure'] == 'public':
            private_flag = False
        else:
            private_flag = True
        dt = datetime.datetime.now()
        pkg_dict_patch = {
            'id': pkg_dict['prepare_dataset_id'],
            #'name': 'gpublish-' + dt.strftime("%Y%m%d%H%M%S")+'-'+ pkg_dict_prepare['name'],
            'name': pkg_dict_prepare['name'],
            'disclosure': pkg_dict['governance_disclosure'],
            'data_category': pkg_dict['governance_data_category'],
            'private': private_flag,
            'allow_harvest': pkg_dict['governance_allow_harvest'],
            'processing_dataset_id': 'finished',
            'publish_dataset_id': pkg_dict['prepare_dataset_id'],
            'finished_governance_state': 'complete' + '[' + pkg_dict['id'] + ']'
        }
        pkg_dict_create = plugins.toolkit.get_action('package_patch')(context, pkg_dict_patch)
        pkg_dict_mo = model.Package.get(pkg_dict['prepare_dataset_id'])
        pkg_dict_mo.type = 'dataset'
        pkg_dict_mo.save()

        from ckan.lib.search import rebuild
        rebuild(pkg_dict['prepare_dataset_id'])
        pkg_dict_patch = {
            'id': pkg_dict['prepare_dataset_id'],
            'extras': []
        }
        pkg_dict_create = plugins.toolkit.get_action('package_patch')(context, pkg_dict_patch)

    except:
        raise ValidationError
    return pkg_dict_create

def _update_dataset(context, data_dict):
    _check_access('package_update', context, data_dict)
    pkg_dict_update = ""
    package_id = _get_or_bust(data_dict, 'id')
    try:
        pkg_dict = plugins.toolkit.get_action('package_show')(None, {'id':package_id}) #get processing
        user_obj = model.User.get(six.ensure_text(pkg_dict['creator_user_id']))
        context = {'model': model, 'session': model.Session, 'ignore_auth': True,
                'user': user_obj.name, 'auth_user_obj': None}
        if pkg_dict['governance_disclosure'] == 'public':
            private_flag = False
        else:
            private_flag = True

        pkg_dict_patch = {
            'id': pkg_dict['prepare_dataset_id'],
            'disclosure': pkg_dict['governance_disclosure'],
            'data_category': pkg_dict['governance_data_category'],
            'private': private_flag,
            'allow_harvest': pkg_dict['governance_allow_harvest'],
            'processing_dataset_id': 'finished',
            'finished_governance_state': 'complete' + '[' + pkg_dict['id'] + ']'
        }
        pkg_prepare_patch = plugins.toolkit.get_action('package_patch')(context, pkg_dict_patch) #patch prepare
        pkg_dict_prepare = plugins.toolkit.get_action('package_show')(None, {'id':pkg_dict['prepare_dataset_id']}) #get prepare
        
        already_archive_old_version = plugins.toolkit.get_action('package_search')(context, {"q":"type:processing +prepare_dataset_id:"+pkg_dict_prepare['publish_dataset_id']+" +name:*garchive-* +governance_state:complete","include_private":True})
        log.info('check already_archive_old_version for complete')
        for pkg in already_archive_old_version.get('results'):
            plugins.toolkit.get_action('package_patch')(context, {"id":pkg['id'], "previous_governance_state":""})
        proc_dict = plugins.toolkit.get_action('package_patch')(context, {'id':pkg_dict['id'], "prepare_dataset_id":pkg_dict_prepare['publish_dataset_id']}) #patch processing

        pkg_dict_original = pkg_dict_prepare.copy()
        pkg_dict_prepare['id'] = pkg_dict_prepare['publish_dataset_id']
        pkg_dict_prepare['name'] = pkg_dict_prepare['name'].replace('gprepare-','')
        pkg_dict_prepare['type'] = 'dataset'
        if pkg_dict_prepare['num_resources'] > 0 :
            del pkg_dict_prepare['resources']
        pkg_dict_prepare['extras'] = pkg_dict_prepare.get('extras',[])

        del pkg_dict_prepare['extras']

        pkg_dict_update = plugins.toolkit.get_action('package_update')(context, pkg_dict_prepare) #update dataset new version

        if pkg_dict_original['num_resources'] > 0 :
            for resourceDict in pkg_dict_original['resources']:
                resourceDict['package_id'] = pkg_dict_update['id']
                temp_prepare_resource_id = resourceDict['id']
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
                        os.popen('cp '+config.get('ckan.storage_path')+'/resources/'+temp_prepare_resource_id[0:3]+'/'+temp_prepare_resource_id[3:6]+'/'+temp_prepare_resource_id[6:]+' '+config.get('ckan.storage_path')+'/resources/'+res_created['id'][0:3]+'/'+res_created['id'][3:6]+'/'+res_created['id'][6:])
                    except OSError as e:
                        # errno 17 is file already exists
                        if e.errno != 17:
                            raise
                else:
                    resourceDict['hash'] = ''
                    res_created = plugins.toolkit.get_action('resource_create')(context, resourceDict) # create resources in prepare

        pkg_dict_delete = plugins.toolkit.get_action('package_delete')(context, {"id":pkg_dict['prepare_dataset_id']})
        pkg_dict_delete = plugins.toolkit.get_action('dataset_purge')(context, {"id":pkg_dict['prepare_dataset_id']})
    except:
        raise ValidationError
    return pkg_dict_update

def processing_update_state(context, data_dict):
    _check_access('sysadmin', context, data_dict)
    pkg_dict_update = ""
    pkg_dict = plugins.toolkit.get_action('package_show')(None, {'id':data_dict['id']}) #get processing
    pkg_dict_prepare =  plugins.toolkit.get_action('package_show')(None, {'id':pkg_dict['prepare_dataset_id']}) #get prepare
    pkg_dict_original = pkg_dict.copy()
    if pkg_dict['type'] == 'processing':
        pkg_dict['previous_governance_state'] = pkg_dict_original['governance_state']
        pkg_dict['governance_data_category'] = data_dict['governance_data_category']
        pkg_dict['governance_state'] = data_dict['governance_state']
        pkg_dict['governance_disclosure'] = data_dict['governance_disclosure']
        if 'governance_allow_harvest' in data_dict:
            pkg_dict['governance_allow_harvest'] = data_dict['governance_allow_harvest']

        pkg_dict['governance_notes'] = data_dict['governance_notes']
        pkg_dict['governance_steward'] = data_dict['governance_steward']
        pkg_dict['governance_date'] = data_dict['governance_date']

        if pkg_dict['governance_state'] == 'reject':
            already_archive = plugins.toolkit.get_action('package_search')(context, {"q":"type:processing +prepare_dataset_id:"+pkg_dict['prepare_dataset_id']+" +name:*garchive-*","include_private":True})
            log.info('check already_archive for reject')
            for pkg in already_archive.get('results'):
                plugins.toolkit.get_action('package_patch')(context, {"id":pkg['id'], "previous_governance_state":""})

            pkg_dict['name'] = pkg_dict['name'].replace('processing-','archive-')
            pkg_dict_update = plugins.toolkit.get_action('package_update')(context, pkg_dict) #update processing
            pkg_dict_prepare['processing_dataset_id'] = ''
            pkg_dict_prepare['finished_governance_state'] = 'reject' + '[' + pkg_dict_update['id'] + ']'
            pkg_dict_update_prepare = plugins.toolkit.get_action('package_update')(context, pkg_dict_prepare) #update prepare

            portal = LocalCKAN()
            activity_dict = {"data": {"actor": six.ensure_text(c.user), "package":pkg_dict_update_prepare, 
                "governance": {"governance_log":"Processing update state","governance_state":pkg_dict['governance_state'],"governance_notes":pkg_dict['governance_notes'],"governance_steward":pkg_dict['governance_steward'],"governance_date":pkg_dict['governance_date']}}, 
                "user_id": pkg_dict_update_prepare.get("creator_user_id"), 
                "object_id": pkg_dict_update_prepare.get("id"), 
                "activity_type": "changed package"
                }
            portal.action.activity_create(**activity_dict)

            myobj = {"user_id": pkg_dict_prepare['creator_user_id'],"package_id": pkg_dict_prepare['id'],"event":"notify_reject_forowner","governance_notes":pkg_dict['governance_notes']}
            plugins.toolkit.get_action('governance_send_mail')(context, myobj)

        elif pkg_dict['governance_state'] == 'complete':
            if pkg_dict_original['governance_state'] != 'wait':
                already_archive = plugins.toolkit.get_action('package_search')(context, {"q":"type:processing +prepare_dataset_id:"+pkg_dict['prepare_dataset_id']+" +name:*garchive-*","include_private":True})
                log.info('check already_archive for complete')
                for pkg in already_archive.get('results'):
                    plugins.toolkit.get_action('package_patch')(context, {"id":pkg['id'], "previous_governance_state":""})

                pkg_dict['name'] = pkg_dict['name'].replace('processing-','archive-')
                pkg_dict['disclosure'] = pkg_dict['governance_disclosure']
                pkg_dict['data_category'] = pkg_dict['governance_data_category']
                pkg_dict['allow_harvest'] = pkg_dict['governance_allow_harvest']
                pkg_dict_update = plugins.toolkit.get_action('package_update')(context, pkg_dict) #update processing
                pkg_dict_prepare = plugins.toolkit.get_action('package_show')(context, {'id':pkg_dict['prepare_dataset_id']}) #get prepare
                if pkg_dict_prepare['name'].startswith('gprepare-') and pkg_dict_prepare.get('publish_dataset_id','') != '':
                    pkg_dataset_return = _update_dataset(context, {'id':pkg_dict['id']}) #update dataset
                else:
                    pkg_dataset_return = _create_dataset(context, {'id':pkg_dict['id']}) #create dataset

                portal = LocalCKAN()
                activity_dict = {"data": {"actor": six.ensure_text(c.user), "package":pkg_dataset_return, 
                    "governance": {"governance_log":"Processing update state","governance_state":pkg_dict['governance_state'],"governance_notes":pkg_dict['governance_notes'],"governance_steward":pkg_dict['governance_steward'],"governance_date":pkg_dict['governance_date']}}, 
                    "user_id": pkg_dataset_return.get("creator_user_id"), 
                    "object_id": pkg_dataset_return.get("id"), 
                    "activity_type": "changed package"
                    }
                portal.action.activity_create(**activity_dict)

                entity = model.Package.get(pkg_dataset_return.get("id"))
                activity = entity.activity_stream_item('changed', pkg_dataset_return.get("creator_user_id"))
                model.Session.add(activity)
                model.Session.commit()
                
                myobj = {"user_id": pkg_dataset_return['creator_user_id'],"package_id": pkg_dataset_return['id'],"event":"notify_complete_forowner","data_category":pkg_dataset_return['data_category'],"disclosure":pkg_dataset_return['disclosure']}
                plugins.toolkit.get_action('governance_send_mail')(context, myobj)

        else:
            pkg_dict_update = plugins.toolkit.get_action('package_update')(context, pkg_dict) #update processing

            portal = LocalCKAN()
            activity_dict = {"data": {"actor": six.ensure_text(c.user), "package":pkg_dict_prepare, 
                "governance": {"governance_log":"Processing update state","governance_state":pkg_dict['governance_state'],"governance_notes":pkg_dict['governance_notes'],"governance_steward":pkg_dict['governance_steward'],"governance_date":pkg_dict['governance_date']}}, 
                "user_id": pkg_dict_prepare.get("creator_user_id"), 
                "object_id": pkg_dict_prepare.get("id"), 
                "activity_type": "changed package"
                }
            portal.action.activity_create(**activity_dict)

            myobj = {"user_id": pkg_dict_prepare['creator_user_id'],"package_id": pkg_dict_prepare['id'],"event":"notify_"+pkg_dict['governance_state']+"_forowner"}
            plugins.toolkit.get_action('governance_send_mail')(context, myobj)

            myobj = {"user_id": pkg_dict_prepare['creator_user_id'],"package_id": pkg_dict_prepare['id'],"event":"notify_"+pkg_dict['governance_state']+"_forsteward"}
            plugins.toolkit.get_action('governance_send_mail')(context, myobj)
    else:
        raise NotFound
         
    return pkg_dict_update
