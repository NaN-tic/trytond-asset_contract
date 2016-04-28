# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Asset', 'ContractLine', 'ContractConsumption']


class Asset:
    __name__ = 'asset'
    __metaclass__ = PoolMeta
    contract_lines = fields.One2Many('contract.line', 'asset',
        'Contract Lines')

    @classmethod
    def copy(cls, assets, default=None):
        if default is None:
            default = {}
        default = default.copy()
        if not 'contract_lines' in default:
            default['contract_lines'] = None
        return super(Asset, cls).copy(assets, default)


class ContractLine:
    __name__ = 'contract.line'
    __metaclass__ = PoolMeta
    asset_party = fields.Function(fields.Many2One('party.party', 'Party'),
        'on_change_with_asset_party')
    asset = fields.Many2One('asset', 'Asset')

    @fields.depends('contract')
    def on_change_with_asset_party(self, name=None):
        if self.contract and self.contract.party:
            return self.contract.party.id


class ContractConsumption:
    __name__ = 'contract.consumption'
    __metaclass__ = PoolMeta
    def get_invoice_line(self):
        line = super(ContractConsumption, self).get_invoice_line()
        if line and self.contract_line.asset:
            line.invoice_asset = self.contract_line.asset
        if hasattr(line, 'on_change_invoice_asset'):
            line.on_change_invoice_asset()
        return line
