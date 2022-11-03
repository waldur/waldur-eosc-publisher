import unittest
from unittest.mock import Mock

from eosc_publisher import provider_utils
from eosc_publisher.marketplace_utils import


class TestOffers(unittest.TestCase):
    def test_get_or_create_eosc_provider(self):
        mock_sync_provider = Mock()
        provider_utils.sync_eosc_provider = mock_sync_provider
        get_or_create_eosc_provider.return_value = {}

        # provider, is_approved = get_or_create_eosc_provider()

        # mock_get_or_create_eosc_provider.assert_called_once()
        # self.assertEqual(True, False)

    # TODO
    def test_get_or_create_eosc_resource_offer(self):
        self.assertEqual(True, True)

    def test_get_or_create_eosc_resource(self):
        self.assertEqual(True, True)

    def test_create_resource(self):
        self.assertEqual(True, True)

    def test_create_offer_for_resource(self):
        self.assertEqual(True, True)

    def test_sync_offer(self):
        self.assertEqual(True, True)

    def test_process_offers(self):
        self.assertEqual(True, True)


if __name__ == "__main__":
    unittest.main()
