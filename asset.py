# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Asset']


class Asset:
    __name__ = 'asset'
    __metaclass__ = PoolMeta
    contract_line = fields.Function(fields.Many2One('contract.line',
            'Current Contract Line'), 'get_contract_line')
    contract_lines = fields.One2Many('contract.line', 'asset',
        'Contract Lines', readonly=True)

    @classmethod
    def copy(cls, assets, default=None):
        if default is None:
            default = {}
        default = default.copy()
        if 'contract_lines' not in default:
            default['contract_lines'] = None
        return super(Asset, cls).copy(assets, default)
