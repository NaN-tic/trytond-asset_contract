import datetime
import unittest
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from proteus import Model, Wizard
from trytond.exceptions import UserError
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear,
                                                 get_accounts)
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

        today = datetime.datetime.combine(datetime.date.today(),
                                          datetime.datetime.min.time())
        datetime.date.today() + relativedelta(days=1)

        # Install module
        activate_modules(['asset_contract', 'account_invoice'])

        # Create company
        _ = create_company()
        company = get_company()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']

        # Create parties
        Party = Model.get('party.party')
        supplier = Party(name='Supplier')
        supplier.save()
        customer = Party(name='Customer')
        customer.save()

        # Create category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name='Category')
        account_category.accounting = True
        account_category.account_revenue = revenue
        account_category.account_expense = expense
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        Product = Model.get('product.product')
        product = Product()
        template = ProductTemplate()
        template.name = 'product'
        template.account_category = account_category
        template.default_uom = unit
        template.type = 'assets'
        template.list_price = Decimal('10')
        template.cost_price_method = 'fixed'
        template.save()
        product, = template.products
        service_product = Product()
        template = ProductTemplate()
        template.name = 'service'
        template.default_uom = unit
        template.type = 'service'
        template.list_price = Decimal('30')
        template.cost_price = Decimal('10')
        template.cost_price_method = 'fixed'
        template.account_category = account_category
        template.save()
        service_product, = template.products
        template = ProductTemplate()
        template.name = 'service 2'
        template.default_uom = unit
        template.type = 'service'
        template.list_price = Decimal('20')
        template.cost_price = Decimal('5')
        template.cost_price_method = 'fixed'
        template.account_category = account_category
        template.save()
        service_product2, = template.products

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()
        customer.customer_payment_term = payment_term
        customer.save()

        # Create an asset
        Asset = Model.get('asset')
        asset = Asset()
        asset.name = 'Asset'
        asset.product = product
        asset.save()
        asset2 = Asset()
        asset2.name = 'Asset 2'
        asset2.product = product
        asset2.save()

        # Create daily service
        Service = Model.get('contract.service')
        service = Service()
        service.product = service_product
        service.name = 'Service'
        service.save()
        service2 = Service()
        service2.product = service_product2
        service2.name = 'Service 2'
        service2.save()

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

        # Create a contract
        Contract = Model.get('contract')
        contract = Contract()
        contract.party = customer
        contract.start_period_date = datetime.date(today.year, 1, 1)
        contract.first_invoice_date = datetime.date(today.year, 1, 1)
        contract.freq = 'monthly'
        contract.interval = 1
        line = contract.lines.new()
        line.service = service
        line.start_date = datetime.date(today.year, 1, 1)
        line.asset = asset
        self.assertEqual(line.unit_price, Decimal('30'))
        contract.click('confirm')
        self.assertEqual(contract.state, 'confirmed')

        # Generate consumed lines
        create_consumptions = Wizard('contract.create_consumptions')
        create_consumptions.form.date = datetime.date(today.year, 1, 31)
        create_consumptions.execute('create_consumptions')

        # Generate invoice for consumed lines
        create_invoice = Wizard('contract.create_invoices')
        create_invoice.form.date = datetime.date(today.year, 1, 31)
        create_invoice.execute('create_invoices')

        # Only one invoice is generated for grouping party
        Invoice = Model.get('account.invoice')
        invoice, = Invoice.find([('party', '=', customer.id)])
        self.assertEqual(invoice.untaxed_amount, Decimal('30.00'))
        invoice_line, = invoice.lines

        # Create a contract with an asset with multiples lines
        Contract = Model.get('contract')
        contract = Contract()
        contract.party = customer
        contract.start_period_date = datetime.date(today.year, 1, 1)
        contract.first_invoice_date = datetime.date(today.year, 1, 1)
        contract.freq = 'monthly'
        contract.interval = 1
        line = contract.lines.new()
        line.service = service
        line.start_date = datetime.date(today.year, 1, 1)
        line.asset = asset2
        line = contract.lines.new()
        line.service = service2
        line.start_date = datetime.date(today.year, 1, 1)
        line.asset = asset2
        contract.click('confirm')
        self.assertEqual(contract.state, 'confirmed')

        # Create a contract with an asset that has assigned in other contract
        Contract = Model.get('contract')
        contract = Contract()
        contract.party = customer
        contract.start_period_date = datetime.date(today.year, 1, 1)
        contract.first_invoice_date = datetime.date(today.year, 1, 1)
        contract.freq = 'monthly'
        contract.interval = 1
        line = contract.lines.new()
        line.service = service
        line.start_date = datetime.date(today.year, 1, 1)
        line.asset = asset2

        with self.assertRaises(UserError):
            contract.click('confirm')
