# -*- coding: utf-8 -*-


import logging

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    ei_notes = fields.Char(string="Notes")
