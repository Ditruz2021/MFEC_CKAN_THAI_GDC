import datetime
import requests
import json
from ckan.common import _, c
from ckan import model
import ckan.plugins as p
import ckan.lib.navl.dictization_functions as df
import ckan.lib.uploader as uploader
import ckan.lib.helpers as h
import ckantoolkit as tk
try:
    from html.parser import HTMLParser
except ImportError:
    from HTMLParser import HTMLParser
from ckanext.pages.logic.schema import update_pages_schema

import ckan.authz as authz

from ckanext.pages import db

import logging

config = tk.config
_ = tk._

log = logging.getLogger(__name__)

class HTMLFirstImage(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.first_image = None

    def handle_starttag(self, tag, attrs):
        if tag == 'img' and not self.first_image:
            self.first_image = dict(attrs)['src']


def _pages_show(context, data_dict):
    org_id = data_dict.get('org_id')
    page = data_dict.get('page')
    out = db.Page.get(group_id=org_id, name=page)
    if out:
        out = db.table_dictize(out, context)
    return out

def _pages_news_show(context, data_dict):
    page = data_dict.get('page')
    out = db.Page.get(name=page)
    if out:
        out = db.table_dictize(out, context)
    return out


def _pages_list(context, data_dict):
    search = {}
    org_id = data_dict.get('org_id')
    ordered = data_dict.get('order')
    order_publish_date = data_dict.get('order_publish_date')
    page_type = data_dict.get('page_type')
    private = data_dict.get('private', True)
    if page_type:
        search['page_type'] = page_type
    if order_publish_date:
        search['order_publish_date'] = True
    if not org_id:
        search['group_id'] = None
        try:
            p.toolkit.check_access('ckanext_pages_update', context, data_dict)
            if not private:
                search['private'] = False
        except p.toolkit.NotAuthorized:
            search['private'] = False
    else:
        group = context['model'].Group.get(org_id)
        user = context['user']
        member = authz.has_user_permission_for_group_or_org(
            group.id, user, 'read')
        search['group_id'] = org_id
        if not member:
            search['private'] = False
    if ordered:
        search['order'] = ordered
        del search['private']
    out = db.Page.pages(**search)
    out_list = []
    for pg in out:
        parser = HTMLFirstImage()
        parser.feed(pg.content)
        img = parser.first_image
        pg_row = {'title': pg.title,
                  'content': pg.content,
                  'name': pg.name,
                  'publish_date': pg.publish_date.isoformat() if pg.publish_date else None,
                  'group_id': pg.group_id,
                  'page_type': pg.page_type,
                  'count': pg.count,
                  'pin': pg.pin,
                  }
        if img:
            pg_row['image'] = img
        extras = pg.extras
        if extras:
            pg_row.update(json.loads(pg.extras))
        out_list.append(pg_row)
    return out_list

def _pages_all_list(context, data_dict):
    search = {}
    ordered = data_dict.get('order')
    order_publish_date = data_dict.get('order_publish_date')
    page_type = data_dict.get('page_type')
    private = data_dict.get('private', True)
    if ordered:
        search['order'] = True
    if page_type:
        search['page_type'] = page_type
    if order_publish_date:
        search['order_publish_date'] = True
        
    out = db.Page.pages(**search)
    out_list = []
    for pg in out:
        parser = HTMLFirstImage()
        parser.feed(pg.content)
        img = parser.first_image
        pg_row = {'title': pg.title,
                  'content': pg.content,
                  'name': pg.name,
                  'publish_date': pg.publish_date.isoformat() if pg.publish_date else None,                  
                  'page_type': pg.page_type,
                  }
        if img:
            pg_row['image'] = img
        extras = pg.extras
        if extras:
            pg_row.update(json.loads(pg.extras))
        out_list.append(pg_row)
    return out_list


def _pages_delete(context, data_dict):
    org_id = data_dict.get('org_id')
    page = data_dict.get('page')
    out = db.Page.get(group_id=org_id, name=page)
    if out:
        session = context['session']
        session.delete(out)
        session.commit()


def _pages_update(context, data_dict):
    org_id = data_dict.get('org_id')
    page = data_dict.get('page')
    # we need the page in the context for name validation
    context['page'] = page
    context['group_id'] = org_id
    schema = update_pages_schema()

    data, errors = df.validate(data_dict, schema, context)

    if errors:
        raise p.toolkit.ValidationError(errors)

    out = db.Page.get(group_id=org_id, name=page)
    if not out:
        out = db.Page()
        out.group_id = org_id
        out.name = page

    items = ['title', 'content', 'name', 'private', 'pin',
             'order', 'page_type', 'publish_date']

    # backward compatible with older version where page_type does not exist
    for item in items:
        setattr(out, item, data.get(item, 'page' if item == 'page_type' else None))

    extras = {}

    extra_keys = set(schema.keys()) - set(items + ['id', 'created'])
    for key in extra_keys:
        if key in data:
            extras[key] = data.get(key)
    out.extras = json.dumps(extras)

    out.modified = datetime.datetime.utcnow()
    user = model.User.get(context['user'])
    out.user_id = user.id
    out.save()
    session = context['session']
    session.add(out)
    session.commit()

    # Conditional API request when saving data
    if out.order in ['1', '2']:
        site_url = config.get('ckan.site_url')  # Replace with your actual site URL
        api_url = site_url + '/api/3/action/ckan_page_delete'
        payload = {
            'name': out.name,
            'order': out.order
        }
        headers = {'Content-type': 'application/json', 'Authorization': c.userobj.apikey}
        response = requests.post(api_url, headers=headers, json=payload)
        
        # Optionally, handle the response
        if response.status_code == 200:
            print("Successfully sent data to API")
        else:
            print("Failed to send data to API. Status code: " + str(response.status_code) + ", Response: " + response.text)
        # Second API request
        api_url_update_pin = site_url + '/api/3/action/update_pin'
        payload_update_pin = {
                'pin': out.pin,
                # Include any other required fields in the payload
        }
        response_update_pin = requests.post(api_url_update_pin, headers=headers, json=payload_update_pin)
        
        # Optionally, handle the response
        if response_update_pin.status_code == 200:
                print("Successfully sent pin update data to API")
        else:
                print("Failed to send pin update data to API. Status code: " + str(response_update_pin.status_code) + ", Response: " + response_update_pin.text)
        # Return the saved page object
    return out


def pages_upload(context, data_dict):
    """ Upload a file to the CKAN server.

    This method implements the logic for file uploads used by CKEditor. For
    more details on implementation and expected return values see:
     - https://ckeditor.com/docs/ckeditor4/latest/guide/dev_file_upload.html#server-side-configuration

    """

    try:
        p.toolkit.check_access('ckanext_pages_upload', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))

    upload = uploader.get_uploader('page_images')

    upload.update_data_dict(data_dict, 'image_url',
                            'upload', 'clear_upload')

    max_image_size = uploader.get_max_image_size()

    try:
        upload.upload(max_image_size)
    except p.toolkit.ValidationError:
        message = (
            "Can't upload the file, size is too large. "
            "(Max allowed is {0}mb)".format(max_image_size)
            )
        return {'uploaded': 0, 'error': {'message': message}}

    image_url = data_dict.get('image_url')
    if image_url and image_url[0:6] not in {'http:/', 'https:'}:
        image_url = h.url_for_static(
            'uploads/page_images/%s' % image_url,
            qualified=True
        )
    return {'url': image_url, 'fileName': upload.filename, 'uploaded': 1}


@tk.side_effect_free
def pages_show(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_pages_show', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_show(context, data_dict)

def pages_news_show(context, data_dict):    
    return _pages_news_show(context, data_dict)


def pages_update(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_pages_update', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_update(context, data_dict)


def pages_delete(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_pages_delete', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_delete(context, data_dict)


@tk.side_effect_free
def pages_list(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_pages_list', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_list(context, data_dict)

def pages_all_list(context, data_dict):    
    return _pages_all_list(context, data_dict)



@tk.side_effect_free
def org_pages_show(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_org_pages_show', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_show(context, data_dict)


def org_pages_update(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_org_pages_update', context,
                               data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_update(context, data_dict)


def org_pages_delete(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_org_pages_delete', context,
                               data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_delete(context, data_dict)


@tk.side_effect_free
def org_pages_list(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_org_pages_list', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_list(context, data_dict)


@tk.side_effect_free
def group_pages_show(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_group_pages_show', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_show(context, data_dict)


def group_pages_update(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_group_pages_update', context,
                               data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_update(context, data_dict)


def group_pages_delete(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_group_pages_delete', context,
                               data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_delete(context, data_dict)


@tk.side_effect_free
def group_pages_list(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_group_pages_list', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_list(context, data_dict) 
