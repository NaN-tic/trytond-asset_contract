# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .contract import *


def register():
    Pool.register(
        ContractLine,
        Asset,
        ShipmentWork,
        ShipmentWorkProduct,
        ContractConsumption,
        module='asset_contract', type_='model')
