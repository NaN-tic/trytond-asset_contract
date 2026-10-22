import datetime
import unittest
from decimal import Decimal

from proteus import Model, Wizard
from trytond.modules.account.tests.tools import (
    create_chart, create_fiscalyear, get_accounts)
from trytond.modules.account_invoice.tests.tools import (
    create_payment_term, set_fiscalyear_invoice_sequences)
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):
        today = datetime.date(2020, 1, 1)

        # Install asset contract with analytics
        activate_modules(['asset_contract', 'analytic_invoice_asset'])

        # Create company
        _ = create_company()
        company = get_company()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company, today))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)

        # Create analytic accounts
        AnalyticAccount = Model.get('analytic_account.account')
        root = AnalyticAccount(type='root', name='Root')
        root.save()
        asset_analytic_account = AnalyticAccount(
            root=root, parent=root, name='Asset Analytic')
        asset_analytic_account.save()
        contract_analytic_account = AnalyticAccount(
            root=root, parent=root, name='Contract Analytic')
        contract_analytic_account.save()

        # Create customer
        payment_term = create_payment_term()
        payment_term.save()
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.customer_payment_term = payment_term
        customer.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name='Category')
        account_category.accounting = True
        account_category.account_revenue = accounts['revenue']
        account_category.account_expense = accounts['expense']
        account_category.save()

        # Create asset and service products
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')

        asset_template = ProductTemplate(
            name='Asset Product', default_uom=unit, type='assets',
            list_price=Decimal('10'), cost_price_method='fixed',
            account_category=account_category)
        asset_template.save()
        asset_product, = asset_template.products

        service_template = ProductTemplate(
            name='Service Product', default_uom=unit, type='service',
            list_price=Decimal('30'), cost_price=Decimal('10'),
            cost_price_method='fixed', account_category=account_category)
        service_template.save()
        service_product, = service_template.products

        # Create an asset with its own analytic account
        Asset = Model.get('asset')
        asset = Asset(name='Asset', product=asset_product)
        asset_entry, = asset.analytic_accounts
        asset_entry.account = asset_analytic_account
        asset.save()

        # Create contract service
        Service = Model.get('contract.service')
        service = Service(name='Service', product=service_product)
        service.save()

        # Configure contract
        Sequence = Model.get('ir.sequence')
        sequence_contract, = Sequence.find([('name', '=', 'Contract')])
        Journal = Model.get('account.journal')
        journal, = Journal.find([('type', '=', 'revenue')])
        ContractConfig = Model.get('contract.configuration')
        contract_config = ContractConfig(1)
        contract_config.contract_sequence = sequence_contract
        contract_config.journal = journal
        contract_config.save()

        # Create contract line with a different analytic account
        Contract = Model.get('contract')
        contract = Contract(
            party=customer,
            start_period_date=today,
            first_invoice_date=today,
            freq='monthly',
            interval=1)
        contract_line = contract.lines.new(
            service=service,
            start_date=today,
            asset=asset)
        contract_entry, = contract_line.analytic_accounts
        contract_entry.account = contract_analytic_account
        contract.click('confirm')

        # Create consumptions and invoice
        create_consumptions = Wizard('contract.create_consumptions')
        create_consumptions.form.date = datetime.date(2020, 1, 31)
        create_consumptions.execute('create_consumptions')

        create_invoices = Wizard('contract.create_invoices')
        create_invoices.form.date = datetime.date(2020, 1, 31)
        create_invoices.execute('create_invoices')

        # Contract line analytics take precedence over asset analytics
        Invoice = Model.get('account.invoice')
        invoice, = Invoice.find([])
        invoice_line, = invoice.lines
        invoice_entry, = invoice_line.analytic_accounts
        self.assertEqual(invoice_line.invoice_asset, asset)
        self.assertEqual(invoice_entry.root, root)
        self.assertEqual(invoice_entry.account, contract_analytic_account)
        self.assertNotEqual(invoice_entry.account, asset_analytic_account)
