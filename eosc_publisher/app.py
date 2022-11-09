from time import sleep

from eosc_publisher import marketplace_utils, provider_utils

from . import WALDUR_TARGET_CUSTOMER_UUID, logger, waldur_client


def process_offers():
    waldur_offerings = waldur_client.list_marketplace_offerings(
        {
            "customer_uuid": WALDUR_TARGET_CUSTOMER_UUID,
            "attributes": '{"enable_sync_to_eosc":true}',
        },
    )

    if len(waldur_offerings) == 0:
        logger.info("There are no offerings ready for sync with EOSC portal.")

    for waldur_offering in waldur_offerings:
        try:
            logger.info("Syncing offering %s", waldur_offering["name"])
            provider = provider_utils.sync_eosc_provider()
            if provider is None:
                continue
            if waldur_offering["state"] in ["Active", "Paused"]:
                provider_contact = provider["users"][-1]
                provider_resource = provider_utils.sync_eosc_resource(
                    waldur_offering, provider_contact, provider["id"]
                )
                marketplace_utils.create_offer_for_waldur_offering(
                    waldur_offering, provider_resource
                )
            elif waldur_offering["state"] in ["Archived", "Draft"]:
                marketplace_utils.deactivate_offer(waldur_offering)
            # if not eosc_resource_created and not is_resource_up_to_date(eosc_resource, waldur_resource):
            #     update_eosc_resource(eosc_resource, waldur_resource)
            # if not offer_created and not are_offers_up_to_date(eosc_resource_offers, waldur_resource):
            #     update_eosc_offers(eosc_resource, waldur_resource)
        except Exception as e:
            logger.exception(
                "The offering %s (%s) can not be published due to the following exception: %s",
                waldur_offering["name"],
                waldur_offering["uuid"],
                e,
            )


def sync_offers():
    while True:
        try:
            process_offers()
        except Exception as e:
            logger.exception(
                "The application crashed due to the following exception: %s", e
            )
        sleep(60 * 10)


if __name__ == "__main__":
    sync_offers()
