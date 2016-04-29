# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .asset import *
from .contract import *


def register():
    Pool.register(
        Asset,
        Contract,
        ContractLine,
        ContractConsumption,
        module='asset_contract', type_='model')
