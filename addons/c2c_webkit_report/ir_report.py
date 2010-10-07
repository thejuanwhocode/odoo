# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Nicolas Bessi (Camptocamp)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv, fields
import netsvc
from webkit_report import WebKitParser
from report.report_sxw import rml_parse
import base64
import tools
from tools.translate import _
import os

def delete_report_service(name):
    "Delete the report of the known services"
    name = 'report.%s' % name
    if netsvc.Service._services.get( name, False ):
        del netsvc.Service._services

def register_report(name, model, tmpl_path, parser):
    "Register the report into the services"
    name = 'report.%s' % name
    if netsvc.Service._services.get(name, False):
        del netsvc.Service._services[name]
    WebKitParser(name, model, tmpl_path, parser=parser)


class ReportXML(osv.osv):
    
    def __init__(self, pool, cr):
        super(ReportXML, self).__init__(pool, cr)
    
    def register_all(self,cursor):
        value = super(ReportXML, self).register_all(cursor)
        cursor.execute("SELECT * FROM ir_act_report_xml")
        records = cursor.dictfetchall()
        for record in records:
            if record['report_type'] == 'webkit':
                parser=rml_parse
                register_report(record['report_name'], record['model'], record['report_rml'], parser)
        return value        

    def _report_content(self, cursor, user, ids, name, arg, context=None):
        """Ask OpenERP for Doc String ??"""
        res = {}
        for report in self.browse(cursor, user, ids, context=context):
            data = report[name + '_data']
            if not data and report[name[:-8]]:
                try:
                    fp = tools.file_open(report[name[:-8]], mode='rb')
                    data = fp.read()
                except:
                    data = False
            res[report.id] = data
        return res

    def unlink(self, cursor, user, ids, context=None):
        """Delete report and unregister it"""
        records = self.read(cursor, user, ids)
        trans_obj = self.pool.get('ir.translation')
        trans_ids = trans_obj.search(
            cursor, 
            user,
            [('type', '=', 'webkit'), ('res_id', 'in', ids)]
        )
        trans_obj.unlink(cursor, user, trans_ids)
        for record in records:
            delete_report_service(record['report_name'])
        records = None
        res = super(ReportXML, self).unlink(
                                            cursor, 
                                            user, 
                                            ids, 
                                            context
                                        )
        return res


    def create(self, cursor, user, vals, context=None):
        "Create report and register it"
        res = super(ReportXML, self).create(cursor, user, vals, context)
        parser=rml_parse
        try:
            register_report(
                                vals['report_name'], 
                                vals['model'], 
                                vals.get('report_rml', False), 
                                parser
                            )
        except Exception, e:
            print e
            raise osv.except_osv(
                                    _('Report registration error !'), 
                                    _('Report was not registered in system !')
                                )
        return res
        
    def write(self, cursor, user, ids, vals, context=None):
        "Edit report and manage it regitration"
        parser=rml_parse
        record = self.read(cursor, user, ids)
        if isinstance(record, list) :
            record =  record[0]
        if vals.get('report_name', False) and \
            vals['report_name']!=record['report_name']:
            delete_report_service(record['report_name'])
            report_name = vals['report_name']
        else:
            report_name = record['report_name']
        try:
            register_report( 
                                report_name, 
                                vals.get('model', record['model']), 
                                vals.get('report_rml', record['report_rml']), 
                                parser
                            )
        except Exception, e:
            print e
            raise osv.except_osv(
                                    _('Report registration error !'), 
                                    _('Report was not registered in system !')
                                )
        res = super(ReportXML, self).write(cursor, user, ids, vals, context)
        return res

    def _report_content_inv(self, cursor, user, inid, 
        name, value, arg, context=None):
        """Ask OpenERP for Doc String ??"""
        
        self.write(cursor, user, inid, {name+'_data': value}, context=context)


    _name = 'ir.actions.report.xml'
    _inherit = 'ir.actions.report.xml'
    _columns = {
        'webkit_header':  fields.property(   
                                            'ir.header_webkit',
                                            type='many2one',
                                            relation='ir.header_webkit',
                                            string='WebKit Header',
                                            help="The header linked to the report",
                                            method=True,
                                            view_load=True,
                                            required=True
                                        ),
        'report_webkit': fields.char( 
                                        'WebKit HTML path',
                                        size=256,
                                    ),
        'webkit_debug' : fields.boolean('Webkit debug'),
        'report_webkit_data': fields.text('WebKit HTML content'),
    }

ReportXML()
