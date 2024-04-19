# encoding: utf-8

import click
import ckanext.thaigdc_governance.utils as utils
import logging
import sys

log = logging.getLogger(__name__)

def get_commands():
    return [governance]

@click.group()
def governance():
    pass

@governance.command()
def init():
    try:
        utils.steward_organization_create()
        utils.migrate_datasets()
        click.secho(u"ThaiGDC Governance initiate complete.", fg=u"green")
    except BaseException as error:
        click.secho(u"ThaiGDC Governance initiate error (please contact email: open-d@nectec.or.th): "+str(error), fg=u"red")

@governance.command()
def clear():
    try:
        utils.clear_all()
        click.secho(u"ThaiGDC Governance clear complete.", fg=u"green")
    except BaseException as error:
        click.secho(u"ThaiGDC Governance clear error (please contact email: open-d@nectec.or.th): "+str(error), fg=u"red")
