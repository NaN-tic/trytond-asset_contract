=======================
Asset Contract Scenario
=======================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts
    >>> from.trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.datetime.combine(datetime.date.today(),
    ...     datetime.datetime.min.time())
    >>> tomorrow = datetime.date.today() + relativedelta(days=1)

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install module::

    >>> Module = Model.get('ir.module')
    >>> module, = Module.find([('name', '=', 'asset_contract')])
    >>> module.click('install')
    >>> module, = Module.find([('name', '=', 'account_invoice')])
    >>> module.click('install')
    >>> Wizard('ir.module.install_upgrade').execute('upgrade')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']

Create parties::

    >>> Party = Model.get('party.party')
    >>> supplier = Party(name='Supplier')
    >>> supplier.save()
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create category::

    >>> ProductCategory = Model.get('product.category')
    >>> category = ProductCategory(name='Category')
    >>> category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.category = category
    >>> template.default_uom = unit
    >>> template.type = 'assets'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('10')
    >>> template.cost_price = Decimal('8')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> product, = template.products

    >>> service_product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'service'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.salable = True
    >>> template.list_price = Decimal('30')
    >>> template.cost_price = Decimal('10')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> service_product, = template.products

    >>> template = ProductTemplate()
    >>> template.name = 'service 2'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.salable = True
    >>> template.list_price = Decimal('20')
    >>> template.cost_price = Decimal('5')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> service_product2, = template.products

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()
    >>> customer.customer_payment_term = payment_term
    >>> customer.save()

Create an asset::

    >>> Asset = Model.get('asset')
    >>> asset = Asset()
    >>> asset.name = 'Asset'
    >>> asset.product = product
    >>> asset.save()
    >>> asset2 = Asset()
    >>> asset2.name = 'Asset 2'
    >>> asset2.product = product
    >>> asset2.save()

Create daily service::

    >>> Service = Model.get('contract.service')
    >>> service = Service()
    >>> service.product = service_product
    >>> service.name = 'Service'
    >>> service.freq = 'daily'
    >>> service.interval = 1
    >>> service.save()
    >>> service2 = Service()
    >>> service2.product = service_product2
    >>> service2.name = 'Service 2'
    >>> service2.freq = 'daily'
    >>> service2.interval = 1
    >>> service2.save()

Configure contract::

    >>> Sequence = Model.get('ir.sequence')
    >>> sequence_contract, = Sequence.find([('code', '=', 'contract')])
    >>> Journal = Model.get('account.journal')
    >>> journal, = Journal.find([('type', '=', 'revenue')])

    >>> ContractConfig = Model.get('contract.configuration')
    >>> contract_config = ContractConfig(1)
    >>> contract_config.contract_sequence = sequence_contract
    >>> contract_config.journal = journal
    >>> contract_config.save()

Create a contract::

    >>> Contract = Model.get('contract')
    >>> contract = Contract()
    >>> contract.party = customer
    >>> contract.start_period_date = datetime.date(today.year, 01, 01)
    >>> contract.first_invoice_date = datetime.date(today.year, 01, 01)
    >>> contract.freq = 'monthly'
    >>> contract.interval = 1
    >>> line = contract.lines.new()
    >>> line.service = service
    >>> line.start_date = datetime.date(today.year, 01, 01)
    >>> line.asset = asset
    >>> line.unit_price
    Decimal('30')
    >>> contract.click('confirm')
    >>> contract.state
    u'confirmed'

Generate consumed lines::

    >>> create_consumptions = Wizard('contract.create_consumptions')
    >>> create_consumptions.form.date = datetime.date(today.year, 01, 31)
    >>> create_consumptions.execute('create_consumptions')

Generate invoice for consumed lines::

    >>> create_invoice = Wizard('contract.create_invoices')
    >>> create_invoice.form.date = datetime.date(today.year, 01, 31)
    >>> create_invoice.execute('create_invoices')

Only one invoice is generated for grouping party::

    >>> Invoice = Model.get('account.invoice')
    >>> invoice, = Invoice.find([('party', '=', customer.id)])
    >>> invoice.untaxed_amount
    Decimal('30.00')
    >>> invoice_line, = invoice.lines

Create a contract with an asset with multiples lines::

    >>> Contract = Model.get('contract')
    >>> contract = Contract()
    >>> contract.party = customer
    >>> contract.start_period_date = datetime.date(today.year, 01, 01)
    >>> contract.first_invoice_date = datetime.date(today.year, 01, 01)
    >>> contract.freq = 'monthly'
    >>> contract.interval = 1
    >>> line = contract.lines.new()
    >>> line.service = service
    >>> line.start_date = datetime.date(today.year, 01, 01)
    >>> line.asset = asset2
    >>> line = contract.lines.new()
    >>> line.service = service2
    >>> line.start_date = datetime.date(today.year, 01, 01)
    >>> line.asset = asset2
    >>> contract.click('confirm')
    >>> contract.state
    u'confirmed'

Create a contract with an asset that has assigned in other contract::

    >>> Contract = Model.get('contract')
    >>> contract = Contract()
    >>> contract.party = customer
    >>> contract.start_period_date = datetime.date(today.year, 01, 01)
    >>> contract.first_invoice_date = datetime.date(today.year, 01, 01)
    >>> contract.freq = 'monthly'
    >>> contract.interval = 1
    >>> line = contract.lines.new()
    >>> line.service = service
    >>> line.start_date = datetime.date(today.year, 01, 01)
    >>> line.asset = asset2
    >>> contract.click('confirm')  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    UserError: .
