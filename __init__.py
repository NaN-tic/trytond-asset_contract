# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import asset
from . import contract


def register():
    Pool.register(
        asset.Asset,
        contract.Contract,
        contract.ContractLine,
        contract.ContractConsumption,
        module='asset_contract', type_='model')
