# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval

__all__ = ['Asset', 'ContractLine', 'ContractConsumption']

__metaclass__ = PoolMeta


class Asset:
    __name__ = 'asset'

    contract_lines = fields.One2Many('contract.line', 'asset',
        'Contract Lines')


class ContractLine:
    __name__ = 'contract.line'

    asset_party = fields.Function(fields.Many2One('party.party', 'Party'),
        'on_change_with_asset_party')
    asset = fields.Many2One('asset', 'Asset', domain=[
            ('owner', '=', Eval('asset_party')),
            ],
        depends=['asset_party'])

    @fields.depends('contract')
    def on_change_with_asset_party(self, name=None):
        if self.contract and self.contract.party:
            return self.contract.party.id


class ContractConsumption:
    __name__ = 'contract.consumption'

    def get_invoice_line(self):
        line = super(ContractConsumption, self).get_invoice_line()
        if line and self.contract_line.asset:
            line.invoice_asset = self.contract_line.asset
        return line
