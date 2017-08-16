# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import datetime
from sql.conditionals import Coalesce
from trytond.model import ModelView, Workflow, fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction

__all__ = ['Contract', 'ContractLine', 'ContractConsumption']


class Contract:
    __name__ = 'contract'
    __metaclass__ = PoolMeta

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirm(cls, contracts):
        super(Contract, cls).confirm(contracts)
        # Check dates after confirmation as check_dates() ensures the contract
        # is in 'confirmed' state.
        for contract in contracts:
            for line in contract.lines:
                line.check_dates()


class ContractLine:
    __name__ = 'contract.line'
    __metaclass__ = PoolMeta
    asset_party = fields.Function(fields.Many2One('party.party', 'Party'),
        'on_change_with_asset_party')
    asset = fields.Many2One('asset', 'Asset')

    @classmethod
    def __setup__(cls):
        super(ContractLine, cls).__setup__()
        cls._error_messages.update({
                'asset_has_contract': ('Contract line "%(contract_line)s" '
                    'is not valid because asset "%(asset)s" is already '
                    'assigned to contract line "%(overlapping_line)s".')
                })

    @fields.depends('contract')
    def on_change_with_asset_party(self, name=None):
        if self.contract and self.contract.party:
            return self.contract.party.id

    @classmethod
    def validate(cls, lines):
        for line in lines:
            line.check_dates()

    def check_dates(self):
        if not self.asset:
            return
        if self.contract.state not in ('confirmed', 'finished'):
            return
        Contract = Pool().get('contract')
        cursor = Transaction().connection.cursor()
        max_date = datetime.date(datetime.MAXYEAR, 12, 31)
        start_date = self.start_date
        end_date = self.end_date or max_date
        table = self.__table__()
        contract = Contract.__table__()
        cursor.execute(*table.join(contract, condition=(table.contract ==
                    contract.id)).select(table.id, where=((
                        (table.start_date <= start_date)
                        & (Coalesce(table.end_date, max_date) >= start_date))
                    | ((table.start_date <= end_date)
                        & (Coalesce(table.end_date, max_date) >= end_date))
                    | ((table.start_date >= start_date)
                        & (Coalesce(table.end_date, max_date) <= end_date)))
                & (contract.state.in_(['confirmed', 'finished']))
                & (table.asset == self.asset.id)
                & (table.id != self.id),
                limit=1))
        overlapping_record = cursor.fetchone()
        if overlapping_record:
            overlapping_line = self.__class__(overlapping_record[0])
            self.raise_user_error('asset_has_contract', {
                    'contract_line': self.rec_name,
                    'asset': self.asset.rec_name,
                    'overlapping_line': overlapping_line.rec_name,
                    })


class ContractConsumption:
    __name__ = 'contract.consumption'
    __metaclass__ = PoolMeta

    def get_invoice_line(self):
        Line = Pool().get('account.invoice.line')
        line = super(ContractConsumption, self).get_invoice_line()
        if (line and self.contract_line.asset
                and hasattr(Line, 'invoice_asset')):
            line.invoice_asset = self.contract_line.asset
        if hasattr(line, 'on_change_invoice_asset'):
            line.on_change_invoice_asset()

        return line
