# encoding: utf-8

import datetime
from six import text_type
from sqlalchemy import orm, types, Column, Table, ForeignKey
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.sql.expression import or_

from ckan.model import (
    meta,
    core,
    extension,
    domain_object,
    types as _types,
)

__all__ = ['PackageRequest', 'package_request_table']

package_request_table = Table('package_request', meta.metadata,
        Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),        
        Column('notes', types.UnicodeText),
        Column('owner_org', types.UnicodeText),
        Column('first_name', types.UnicodeText),
        Column('last_name', types.UnicodeText),
        Column('objective', types.UnicodeText),
        Column('package_name', types.UnicodeText),
        Column('email', types.UnicodeText),
        Column('scope', types.UnicodeText),        
        Column('created', types.DateTime, default=datetime.datetime.utcnow),
        Column('modified', types.DateTime, default=datetime.datetime.utcnow),
        Column('send_data', types.Boolean, default=False)
)


class PackageRequest(core.StatefulObjectMixin,
           domain_object.DomainObject):

    def __init__(self, **kw):
        from ckan import model
        super(PackageRequest, self).__init__(**kw)

    @classmethod
    def search_by_name(cls, text_query):
        text_query = text_query
        return meta.Session.query(cls).filter(cls.package_name.contains(text_query.lower()))
    
    @classmethod
    def search(cls, querystr, sqlalchemy_query=None,):        
        if sqlalchemy_query is None:
            query = meta.Session.query(cls)
        else:
            query = sqlalchemy_query
        qstr = '%' + querystr + '%'
        filters = [
            cls.package_name.ilike(qstr),
            cls.first_name.ilike(qstr),
            cls.last_name.ilike(qstr),
            cls.email.ilike(qstr),
        ]
        
        query = query.filter(or_(*filters))
        return query
        
    @classmethod
    def get(cls, reference):
        query = meta.Session.query(cls).autoflush(False)
        query = query.filter(cls.id == reference)
        return query.first()

    @classmethod
    def all(cls, group_type=None):
        """
        Returns all groups.
        """
        q = meta.Session.query(cls)
        return q.order_by(cls.created)

    @property
    def display_name(self):
        if self.fullname is not None and len(self.fullname.strip()) > 0:
            return self.fullname
        return self.name   
meta.mapper(PackageRequest, package_request_table)   

# meta.mapper(PackageRequest, package_request_table,            
#     order_by=package_request_table.c.created,
#     extension=[extension.PluginMapperExtension()])



