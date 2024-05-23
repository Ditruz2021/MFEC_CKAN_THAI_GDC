import ckan.plugins as p
from ckanext.pages.validators import page_name_validator, not_empty_if_blog
from ckanext.pages.interfaces import IPagesSchema


def default_pages_schema():
    ignore_empty = p.toolkit.get_validator('ignore_empty')
    ignore_missing = p.toolkit.get_validator('ignore_missing')
    not_empty = p.toolkit.get_validator('not_empty')
    isodate = p.toolkit.get_validator('isodate')
    name_validator = p.toolkit.get_validator('name_validator')
    try:
        unicode_safe = p.toolkit.get_validator('unicode_safe')
    except p.toolkit.UnknownValidator:
        # CKAN 2.7
        unicode_safe = unicode  # noqa: F821
    return {
        'id': [ignore_empty, unicode_safe],
        'title': [not_empty, unicode_safe],
        'name': [
            not_empty, unicode_safe, name_validator, page_name_validator],
        'content': [ignore_missing, unicode_safe],
        'page_type': [ignore_missing, unicode_safe],
        'order': [ignore_missing, unicode_safe],
        'pin': [ignore_missing],
        'private': [ignore_missing,
                    p.toolkit.get_validator('boolean_validator')],
        'group_id': [ignore_missing, unicode_safe],
        'user_id': [ignore_missing, unicode_safe],
        'created': [ignore_missing, isodate],
        'publish_date': [
            not_empty_if_blog, ignore_missing, isodate],
    }


def update_pages_schema():
    '''
    Returns the schema for the pages fields that can be added by other
    extensions.

    By default these are the keys of the
    :py:func:`ckanext.logic.schema.default_pages_schema`.
    Extensions can add or remove keys from this schema using the
    :py:meth:`ckanext.pages.interfaces.IPagesSchema.update_pages_schema`
    method.

    :returns: a dictionary mapping fields keys to lists of validator and
    converter functions to be applied to those fields
    :rtype: dictionary
    '''

    schema = default_pages_schema()
    for plugin in p.PluginImplementations(IPagesSchema):
        if hasattr(plugin, 'update_pages_schema'):
            schema = plugin.update_pages_schema(schema)

    return schema

def default_page_read_schema(
        duplicate_extras_key, ignore, empty_if_not_sysadmin, ignore_missing,is_positive_integer,
        unicode_safe, package_id_does_not_exist, not_empty,
        boolean_validator, datasets_with_no_organization_cannot_be_private, isodate):
    return {
        '__before': [duplicate_extras_key, ignore],
        'id': [empty_if_not_sysadmin, ignore_missing, unicode_safe,
               package_id_does_not_exist],
        'name': [ignore_missing, unicode_safe,not_empty],        
        'title': [ignore_missing, unicode_safe,not_empty],        
        'content': [ignore_missing, unicode_safe,not_empty],
        'lang': [ignore_missing, unicode_safe,not_empty],
        'order': [ignore_missing, unicode_safe,not_empty],
        'count': [ignore],
        'pin': [ignore],
        'private': [ignore_missing, boolean_validator,
                    datasets_with_no_organization_cannot_be_private],
        'group_id': [ignore_missing, unicode_safe,not_empty],
        'user_id': [ignore_missing, unicode_safe,not_empty],
        'publish_date': [ignore_missing, isodate],
        'page_type': [ignore_missing, unicode_safe,not_empty],
        'created': [ignore_missing, isodate],
        'modified': [ignore_missing, isodate],    
        'extras': [ignore_missing, unicode_safe,not_empty],
        'countread': [ignore_missing, is_positive_integer],
        '__extras': [ignore],

    }

def default_update_page_read_schema():
    schema = default_page_read_schema()
    schema['id'] = []
    schema['countread'] = []

    return schema 
