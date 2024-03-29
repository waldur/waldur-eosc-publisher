from collections import defaultdict
from time import sleep

from eosc_publisher import marketplace_utils, provider_utils

from . import logger, waldur_client


def process_offers():
    waldur_offerings = waldur_client.list_marketplace_provider_offerings()

    if len(waldur_offerings) == 0:
        logger.info("There are no offerings ready for sync with EOSC portal.")

    customer_to_offerings_mapping = defaultdict(lambda: [])
    for waldur_offering in waldur_offerings:
        customer_uuid = waldur_offering["customer_uuid"]
        customer_to_offerings_mapping[customer_uuid].append(waldur_offering)

    eosc_resources = provider_utils.fetch_all_resources_from_eosc_catalogue()
    if not eosc_resources:
        return
    for (
        customer_uuid,
        waldur_customer_offerings,
    ) in customer_to_offerings_mapping.items():
        try:
            logger.info(
                "Processing customer %s [uuid=%s]",
                waldur_customer_offerings[0]["customer_name"],
                customer_uuid,
            )
            waldur_customer = waldur_client._get_resource(
                waldur_client.Endpoints.Customers, customer_uuid
            )

            existing_provider = provider_utils.get_eosc_provider(waldur_customer)
            if existing_provider is None and all(
                [
                    offering["state"] in ["Archived", "Draft"]
                    for offering in waldur_customer_offerings
                ]
            ):
                logger.info(
                    "The provider does not exist and all the offerings are inactive. Skipping the customer."
                )
                logger.info("-" * 20)
                continue

            provider = provider_utils.sync_eosc_provider(
                waldur_customer, existing_provider
            )

            logger.info(
                "Syncing %s offerings of the provider", len(waldur_customer_offerings)
            )

            # TODO: add an ID value to customer.backend_id field
            provider_id = provider["id"]

            for waldur_offering in waldur_customer_offerings:
                logger.info(
                    "Syncing offering %s from %s",
                    waldur_offering["name"],
                    waldur_offering["customer_name"],
                )

                if waldur_offering["state"] in ["Active", "Paused"]:
                    logger.info(
                        "Syncing resource for offering %s", waldur_offering["name"]
                    )

                    # TODO: use the value from options for lookup instead of name
                    if waldur_offering["name"] in eosc_resources:
                        resource_id = eosc_resources[waldur_offering["name"]]
                        provider_resource = provider_utils.update_eosc_resource(
                            waldur_offering, provider_id, resource_id
                        )
                    else:
                        provider_resource = provider_utils.create_eosc_resource(
                            waldur_offering, provider_id
                        )

                    marketplace_utils.sync_marketplace_offer(
                        waldur_offering, provider_resource
                    )
                elif waldur_offering["state"] in ["Archived", "Draft"]:
                    if waldur_offering["name"] in eosc_resources:
                        resource_id = eosc_resources[waldur_offering["name"]]
                        provider_utils.delete_eosc_resource(resource_id)
                        marketplace_utils.deactivate_offer(waldur_offering)
                    else:
                        logger.info("The resource is missing, skipping deletion.")
                logger.info("." * 20)
                # if not eosc_resource_created and not is_resource_up_to_date(eosc_resource, waldur_resource):
                #     update_eosc_resource(eosc_resource, waldur_resource)
                # if not offer_created and not are_offers_up_to_date(eosc_resource_offers, waldur_resource):
                #     update_eosc_offers(eosc_resource, waldur_resource)
        except Exception as e:
            logger.exception(
                "The customer [uuid=%s] and its offerings can not be processed due to the following exception: %s",
                customer_uuid,
                e,
            )
        logger.info("-" * 20)


def sync_offers():
    while True:
        try:
            process_offers()
        except Exception as e:
            logger.exception(
                "The application crashed due to the following exception: %s", e
            )
        logger.info("/" * 20)
        sleep(60 * 10)


if __name__ == "__main__":
    sync_offers()
