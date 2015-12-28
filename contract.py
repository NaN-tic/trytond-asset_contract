# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval, If, Bool

__all__ = ['Asset', 'ShipmentWork', 'ShipmentWorkProduct', 'ContractLine',
    'ContractConsumption']

__metaclass__ = PoolMeta


class Asset:
    __name__ = 'asset'

    shipments = fields.One2Many('shipment.work', 'asset', 'Work Shipments')
    contract_lines = fields.One2Many('contract.line', 'asset',
        'Contract Lines')


class ShipmentWork:
    __name__ = 'shipment.work'

    asset = fields.Many2One('asset', 'Asset',
        domain=[
            If(Bool(Eval('party')), [('owner', '=', Eval('party'))], []),
            ],
        states={
            'required': ~Eval('state').in_(['draft', 'pending', 'cancel']),
            'readonly': Eval('state').in_(['cancel', 'done', 'checked']),
            },
        depends=['party', 'state'])

    @fields.depends('asset', 'employees')
    def on_change_asset(self):
        changes = {}
        if self.asset:
            if (hasattr(self.asset, 'zone') and self.asset.zone and
                    self.asset.zone.employee):
                changes['employees'] = [self.asset.zone.employee.id]
            if self.asset.owner:
                changes['party'] = self.asset.owner.id
        return changes


class ShipmentWorkProduct:
    __name__ = 'shipment.work.product'

    def get_sale_line(self, sale, invoice_method):
        line = super(ShipmentWorkProduct, self).get_sale_line(
                sale, invoice_method)
        if not line:
            return
        line.asset = self.shipment.asset
        return line


class ContractLine:
    __name__ = 'contract.line'

    asset_party = fields.Function(fields.Many2One('party.party', 'Party'),
        'on_change_with_asset_party')
    asset = fields.Many2One('asset', 'Asset', domain=[
            ('owner', '=', Eval('asset_party')),
            ],
        depends=['asset_party'])

    @classmethod
    def __setup__(cls):
        super(ContractLine, cls).__setup__()
        cls._error_messages.update({
                'no_asset_owner': ('Asset "%s" has no owner and it is required'
                    ' in order to generate their maintenances'),
                })

    @fields.depends('contract')
    def on_change_with_asset_party(self, name=None):
        if self.contract:
            return self.contract.party.id

    def get_shipment_work(self, planned_date):
        shipment = super(ContractLine, self).get_shipment_work(planned_date)
        shipment.asset = self.asset
        shipment.party = self.asset.owner
        if self.asset.owner and self.asset.owner.customer_payment_term:
            shipment.payment_term = self.asset.owner.customer_payment_term
        # Compatibilty with aset_zone module:
        if hasattr(self.asset, 'zone') and self.asset.zone and \
                self.asset.zone.employee:
            shipment.employees = [self.asset.zone.employee]
        return shipment


class ContractConsumption:
    __name__ = 'contract.consumption'

    def get_invoice_line(self):
        line = super(ContractConsumption, self).get_invoice_line()
        if line and self.contract_line.asset:
            line.invoice_asset = self.contract_line.asset
        return line
