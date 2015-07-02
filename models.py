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

from datetime import timedelta
from openerp import models, fields, api, exceptions, _

## Classe Course adicionada
class Course(models.Model):
    _name = 'openacademy.course'

    name = fields.Char(string="Title", required=true)
    description = fields.Text()

    responsible_id = fields.Many2one('res.users', ondelete='set null', string="Responsible", index=True)
    
    session_ids = fields.One2many(
        'openacademy.session', 'course_id', string="Sessions")

# Since we added a constraint for the Course name uniqueness, it is not possible to use the
# "duplicate" function anymore (Form ‣ Duplicate).

# Re-implement your own "copy" method which allows to duplicate the Course object, changing
# the original name into "Copy of [original name]".

    @api.one
    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [('name', '=like', _(u"Copy of {}%").format(self.name))])
        if not copied_count:
            new_name = _(u"Copy of {}").format(self.name)
        else:
            new_name = _(u"Copy of {} ({})").format(self.name, copied_count)

        default['name'] = new_name
        return super(Course, self).copy(default)


# CHECK that the course description and the course title are different
# Make the Course's name UNIQUE

    _sql_constraints = [
        ('name_description_check',
         'CHECK(name != description)',
         "The title of the course should not be the description"),

        ('name_unique',
         'UNIQUE(name)',
         "The course title must be unique"),
    ]


## Classe Session criada
class Session(models.Model):
    _name = 'openacademy.session'

    name = fields.Char(required=True)
    start_date = fields.Date(default=fields.Date.today)
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    seats = fields.Integer(string="Number of seats")
    active = fields.Boolean(default=True)
    
# Add an integer color field to the Session model
    color = fields.Integer()

    instructor_id = fields.Many2one('res.partner', string="Instructor",
        domain=['|', ('instructor', '=', True),
                     ('category_id.name', 'ilike', "Teacher")])
    course_id = fields.Many2one('openacademy.course',
        ondelete='cascade', string="Course", required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")

    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')

    end_date = fields.Date(string="End Date", store=True,
        compute='_get_end_date', inverse='_set_end_date')

# Create a computed field expressing the session's duration in hours
    hours = fields.Float(string="Duration in hours",
                         compute='_get_hours', inverse='_set_hours')


# Add the number of attendees as a stored computed field
    attendees_count = fields.Integer(
        string="Attendees count", compute='_get_attendees_count', store=True)


# Add a new state field
# Add state-transitioning methods, those can be called from view buttons to change the record's state
# Add the relevant buttons to the session's form view
    state = fields.Selection([
         ('draft', "Draft"),
         ('confirmed', "Confirmed"),
         ('done', "Done"),
    ])

    @api.one
    def action_draft(self):
        self.state = 'draft'

    @api.one
    def action_confirm(self):
        self.state = 'confirmed'

    @api.one
    def action_done(self):
        self.state = 'done'


    @api.one
    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        if not self.seats:
            self.taken_seats = 0.0
        else:
            self.taken_seats = 100.0 * len(self.attendee_ids) / self.seats

    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': _("Incorrect 'seats' value"),
                    'message': _("The number of available seats may not be negative"),
                },
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': _("Too many attendees"),
                    'message': _("Increase seats or remove excess attendees"),
                },
            }

# add the calendar view to the Session model's actions

    @api.one
    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        if not (self.start_date and self.duration):
            self.end_date = self.start_date
            return

        # Add duration to start_date, but: Monday + 5 days = Saturday, so
        # subtract one second to get on Friday instead
        start = fields.Datetime.from_string(self.start_date)
        duration = timedelta(days=self.duration, seconds=-1)
        self.end_date = start + duration

    @api.one
    def _set_end_date(self):
        if not (self.start_date and self.end_date):
            return

        # Compute the difference between dates, but: Friday - Monday = 4 days,
        # so add one day to get 5 days instead
        start_date = fields.Datetime.from_string(self.start_date)
        end_date = fields.Datetime.from_string(self.end_date)
        self.duration = (end_date - start_date).days + 1

    
# Add the gantt view's definition, and add the gantt view to the Session model's action
    @api.one
    @api.depends('duration')
    def _get_hours(self):
        self.hours = self.duration * 24

    @api.one
    def _set_hours(self):
        self.duration = self.hours / 24


# add the relevant view
    @api.one
    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        self.attendees_count = len(self.attendee_ids)





    # Add a constraint that checks that the instructor is not present in the attendees of his/her own session.
    @api.one
    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        if self.instructor_id and self.instructor_id in self.attendee_ids:
            raise exceptions.ValidationError(_("A session's instructor can't be an attendee"))



    