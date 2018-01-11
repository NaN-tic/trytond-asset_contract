# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
try:
    from trytond.modules.asset_contract.tests.test_asset_contract import suite
except ImportError:
    from .test_asset_contract import suite

__all__ = ['suite']
