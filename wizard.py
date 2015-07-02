# -*- coding: utf-8 -*-

################################################################################
#                                                                              #
# Copyright (C) 2015  Marcelo Costa  - COMDESK Tecnologia                      #
#                                                                              #
# This program is free software: you can redistribute it and/or modify         #
# it under the terms of the GNU Affero General Public License as published by  #
# the Free Software Foundation, either version 3 of the License, or            #
# (at your option) any later version.                                          #
#                                                                              #
# This program is distributed in the hope that it will be useful,              #
# but WITHOUT ANY WARRANTY; without even the implied warranty of               #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
# GNU Affero General Public License for more details.                          #
#                                                                              #
# You should have received a copy of the GNU Affero General Public License     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
#                                                                              #
################################################################################


from openerp import models, fields, api

class Wizard(models.TransientModel):
    _name = 'openacademy.wizard'

# Modify the wizard model so that attendees can be registered to multiple sessions.
    def _default_sessions(self):
        return self.env['openacademy.session'].browse(self._context.get('active_ids'))


    session_ids = fields.Many2many('openacademy.session',
        string="Sessions", required=True, default=_default_sessions)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")


    @api.multi
    def subscribe(self):
        for session in self.session_ids:
            session.attendee_ids |= self.attendee_ids
        return {}
