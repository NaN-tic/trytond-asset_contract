# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Asset']


class Asset(metaclass=PoolMeta):
    __name__ = 'asset'
    contract_lines = fields.One2Many('contract.line', 'asset',
        'Contract Lines', readonly=True)

    @classmethod
    def copy(cls, assets, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default.setdefault('contract_lines')
        return super(Asset, cls).copy(assets, default)
