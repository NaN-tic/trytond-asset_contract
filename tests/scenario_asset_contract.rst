=============
Sale Scenario
=============

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
    >>> product.template = template
    >>> product.save()

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
    >>> service_product.template = template
    >>> service_product.save()

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

Create daily service::

    >>> Service = Model.get('contract.service')
    >>> service = Service()
    >>> service.product = service_product
    >>> service.name = 'Service'
    >>> service.freq = 'daily'
    >>> service.interval = 1
    >>> service.save()

Create a contract::

    >>> Contract = Model.get('contract')
    >>> contract = Contract()
    >>> contract.party = customer
    >>> contract.start_period_date = datetime.date(today.year, 01, 01)
    >>> contract.start_date = datetime.date(today.year, 01, 01)
    >>> contract.freq = 'monthly'
    >>> line = contract.lines.new()
    >>> line.start_date = datetime.date(today.year, 01, 01)
    >>> line.first_invoice_date = datetime.date(today.year, 01, 31)
    >>> line.asset = asset
    >>> line.service = service
    >>> line.unit_price
    Decimal('30')
    >>> contract.click('validate_contract')
    >>> contract.state
    u'validated'

Generate consumed lines::

    >>> create_consumptions = Wizard('contract.create_consumptions')
    >>> create_consumptions.form.date = datetime.date(today.year, 02, 01)
    >>> create_consumptions.execute('create_consumptions')

Generate invoice for consumed lines::

    >>> create_invoice = Wizard('contract.create_invoices')
    >>> create_invoice.form.date = datetime.date(today.year, 02, 01)
    >>> create_invoice.execute('create_invoices')

Only one invoice is generated for grouping party::

    >>> Invoice = Model.get('account.invoice')
    >>> invoice, = Invoice.find([('party', '=', customer.id)])
    >>> invoice.untaxed_amount
    Decimal('30.00')
    >>> invoice_line, = invoice.lines
    >>> invoice_line.invoice_asset == asset
    True

