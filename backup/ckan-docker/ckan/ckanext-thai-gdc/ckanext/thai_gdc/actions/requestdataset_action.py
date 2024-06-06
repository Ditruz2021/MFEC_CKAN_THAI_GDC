import ckan.plugins as p
import ckan.lib.navl.dictization_functions as df


import logging
log = logging.getLogger(__name__)

event_schema = {
    'first_name': [p.toolkit.get_validator('not_empty'), unicode],
    'last_name': [p.toolkit.get_validator('not_empty'), unicode],
    'email': [p.toolkit.get_validator('not_empty'), unicode],
    'owner_org': [p.toolkit.get_validator('not_empty'), unicode],
    'package_name': [p.toolkit.get_validator('not_empty'), unicode],
    'notes': [p.toolkit.get_validator('not_empty'), unicode],
    'scope': [p.toolkit.get_validator('not_empty'), unicode],
    'objective': [p.toolkit.get_validator('not_empty'), unicode],
    'modified': [p.toolkit.get_validator('not_empty'), unicode],
}


def validate_request_dataset(context, data_dict):
    fields = p.toolkit.get_or_bust(data_dict, 'fields')
    data, errors = df.validate(fields, event_schema, context)
    if errors:
        raise p.toolkit.ValidationError(errors)

