# encoding: utf-8

from logging import getLogger

import ckan.plugins as p, datetime
from ckanext.opendstats import blueprint, cli
from ckan.lib.plugins import DefaultTranslation
from ckanext.opendstats import helpers as ops_h

log = getLogger(__name__)

def date_range():
    return list(reversed(range(2020,datetime.datetime.now().year+1)))

class OpendstatsPlugin(p.SingletonPlugin, DefaultTranslation):
    p.implements(p.ITranslation)
    p.implements(p.IConfigurer)
    p.implements(p.IBlueprint)
    p.implements(p.IClick)
    p.implements(p.ITemplateHelpers)

    # IClick
    def get_commands(self):
        return cli.get_commands()

    def get_blueprint(self):
        return blueprint.stats_route

    # IConfigurer
    def update_config(self, config_):
        p.toolkit.add_template_directory(config_, 'templates')
        p.toolkit.add_public_directory(config_, 'public')
        p.toolkit.add_resource('public/ckanext/opendstats', 'opendstats')

        config_['opendstats.special_group'] = config_.get('opendstats.special_group', False)
        config_['opendstats.external_dashboard'] = config_.get('opendstats.external_dashboard', False)
        config_['opendstats.external_dashboard_url'] = config_.get('opendstats.external_dashboard_url', None)

    
    def get_helpers(self):
        return {
            'ops_check_plugin': ops_h.check_plugin,
            'ops_check_table_column': ops_h.check_table_column,
            'date_range': date_range
        }
