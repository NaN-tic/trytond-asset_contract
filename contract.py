# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import datetime
from sql.conditionals import Coalesce
from trytond.model import ModelView, Workflow, fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['Contract', 'ContractLine', 'ContractConsumption']


class Contract(metaclass=PoolMeta):
    __name__ = 'contract'

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


class ContractLine(metaclass=PoolMeta):
    __name__ = 'contract.line'
    asset_party = fields.Function(fields.Many2One('party.party', 'Party'),
        'on_change_with_asset_party')
    asset = fields.Many2One('asset', 'Asset')

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
                & (table.contract != self.contract.id)
                & (table.id != self.id),
                limit=1))
        overlapping_record = cursor.fetchone()
        if overlapping_record:
            overlapping_line = self.__class__(overlapping_record[0])
            raise UserError(gettext('asset_contract.asset_has_contract',
                    contract_line=self.rec_name,
                    asset=self.asset.rec_name,
                    overlapping_line=overlapping_line.rec_name))


class ContractConsumption(metaclass=PoolMeta):
    __name__ = 'contract.consumption'

    def get_invoice_line(self):
        Line = Pool().get('account.invoice.line')
        line = super(ContractConsumption, self).get_invoice_line()
        if (line and self.contract_line.asset
                and hasattr(Line, 'invoice_asset')):
            line.invoice_asset = self.contract_line.asset
        if hasattr(line, 'on_change_invoice_asset'):
            line.on_change_invoice_asset()

        return line
