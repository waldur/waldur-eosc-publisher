import json
import urllib.parse

import requests
from requests.status_codes import codes as http_codes

from . import (
    EOSC_MARKETPLACE_BASE_URL,
    EOSC_MARKETPLACE_OFFERING_TOKEN,
    OFFER_LIST_URL,
    OFFER_URL,
    RESOURCE_LIST_URL,
    RESOURCE_URL,
    WALDUR_API_URL,
    logger,
)


def resource_and_offering_request():
    headers = {
        "accept": "application/json",
        "X-User-Token": EOSC_MARKETPLACE_OFFERING_TOKEN,
    }
    return headers


def offering_request_post_patch(
    offer_name: str, offer_description: str, offer_parameters, internal=True
):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-User-Token": EOSC_MARKETPLACE_OFFERING_TOKEN,
    }
    data = {
        "name": offer_name,
        "description": offer_description,
        "order_type": "order_required",
        "primary_oms_id": 2,
        "oms_params": {},
        "order_url": WALDUR_API_URL.replace(
            "https://api.", "https://"
        ),  # plan['url'],  # "is not a valid URL"
        "internal": internal,
        "parameters": offer_parameters,
    }
    return headers, data


def offering_request_delete():
    headers = {
        "accept": "*/*",
        "X-User-Token": EOSC_MARKETPLACE_OFFERING_TOKEN,
    }
    # TODO: finish
    return headers


def get_resource_list():
    headers = resource_and_offering_request()
    response = requests.get(
        urllib.parse.urljoin(EOSC_MARKETPLACE_BASE_URL, RESOURCE_LIST_URL),
        headers=headers,
    )
    resource_list_data = response.json()
    return resource_list_data


def get_resource(resource_id):
    headers = resource_and_offering_request()
    response = requests.get(
        urllib.parse.urljoin(
            EOSC_MARKETPLACE_BASE_URL, RESOURCE_URL % (str(resource_id))
        ),
        headers=headers,
    )
    resource_data = response.json()
    return resource_data


def get_offer_list_of_resource(resource_id):
    headers = resource_and_offering_request()
    response = requests.get(
        urllib.parse.urljoin(
            EOSC_MARKETPLACE_BASE_URL, OFFER_LIST_URL % (str(resource_id))
        ),
        headers=headers,
    )
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Response status code: {response.status_code}")
        raise requests.exceptions.RequestException


def create_offer_for_resource(
    eosc_resource_id: str,
    offer_name: str,
    offer_description: str,
    offer_parameters,
    internal=True,
):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-User-Token": EOSC_MARKETPLACE_OFFERING_TOKEN,
    }
    data = {
        "name": offer_name,
        "description": offer_description or "N/A",
        "order_type": "order_required",
        "primary_oms_id": 2,
        "oms_params": {},
        "order_url": WALDUR_API_URL.replace(
            "https://api.", "https://"
        ),  # plan['url'],  # "is not a valid URL"
        "internal": internal,
        "parameters": offer_parameters,
    }

    response = requests.post(
        urllib.parse.urljoin(
            EOSC_MARKETPLACE_BASE_URL, OFFER_LIST_URL % eosc_resource_id
        ),
        headers=headers,
        data=json.dumps(data),
    )
    if response.status_code != 201:
        logger.error("Failed to create an offer.", response.status_code, response.text)
    else:
        offer_data = response.json()
        logger.info(f"Successfully created offer {offer_name} for {eosc_resource_id}.")
        return offer_data


def patch_offer_from_resource(
    resource_id, offer_id, waldur_offering_data, offer_description, offer_parameters
):
    headers, data = offering_request_post_patch(
        offer_name=waldur_offering_data,
        offer_description=offer_description,
        offer_parameters=offer_parameters,
    )
    response = requests.patch(
        urllib.parse.urljoin(
            EOSC_MARKETPLACE_BASE_URL, OFFER_URL % (str(resource_id), str(offer_id))
        ),
        headers=headers,
        data=data,
    )
    patch_offer_data = response.json()
    return patch_offer_data


def delete_offer_from_resource(resource_id, offer_id):
    headers = offering_request_delete()
    response = requests.delete(
        urllib.parse.urljoin(
            EOSC_MARKETPLACE_BASE_URL, OFFER_URL % (str(resource_id), str(offer_id))
        ),
        headers=headers,
    )
    delete_offer_data = response.json()
    return delete_offer_data


def _normalize_limits(limit, limit_type):
    if limit is None:
        limit = 0
        return limit
    if limit_type in ["storage", "ram"]:
        return int(limit / 1024)
    return limit


def sync_offer(eosc_resource_id, waldur_offering):
    eosc_offers = get_offer_list_of_resource(eosc_resource_id)["offers"]
    eosc_offers_names = {offer["name"] for offer in eosc_offers}
    for plan in waldur_offering["plans"]:
        if plan["name"] in eosc_offers_names:
            logger.info(
                f"Skipping creation of plan {plan['name']}. Offer with the same name already exists."
            )
            continue

        parameters = [
            {
                "id": "name",
                "label": "Name",
                "description": "Name will be visible in accounting",
                "type": "input",
                "value_type": "string",
                "unit": "",
            }
        ]
        for component in waldur_offering["components"]:
            if component["billing_type"] == "limit":
                parameters.append(
                    {
                        "id": "limit " + component["type"],
                        "label": component["name"],
                        "description": component["description"]
                        or f"Amount of {component['name']} in " f"{plan['name']}.",
                        "type": "range",
                        "value_type": "integer",  # waldur only expects numeric values for limit-type components
                        "unit": component["measured_unit"],
                        "config": {
                            "minimum": _normalize_limits(
                                component["min_value"], component["type"]
                            ),
                            "maximum": _normalize_limits(
                                component["max_value"], component["type"]
                            ),
                            "exclusiveMinimum": False,
                            "exclusiveMaximum": False,
                        },
                    },
                )
            if component["billing_type"] == "usage":
                parameters.append(
                    {
                        "id": "attributes " + component["type"],
                        "label": component["name"],
                        "description": component["description"]
                        or f"Amount of {component['name']} in "
                        f"{waldur_offering['name']}.",
                        "type": "range",
                        "value_type": "integer",  # waldur only expects numeric values for limit-type components
                        "unit": component["measured_unit"],
                        "config": {
                            "minimum": _normalize_limits(
                                component["min_value"], component["type"]
                            ),
                            "maximum": _normalize_limits(
                                component["max_value"], component["type"]
                            ),
                            "exclusiveMinimum": False,
                            "exclusiveMaximum": False,
                        },
                    },
                )

        return create_offer_for_resource(
            eosc_resource_id=eosc_resource_id,
            offer_name=plan["name"],
            offer_description=plan["description"],
            offer_parameters=parameters,
        )


def get_all_offers_from_resource(eosc_resource_id):
    headers = {
        "accept": "application/json",
        "X-User-Token": EOSC_MARKETPLACE_OFFERING_TOKEN,
    }
    response = requests.get(
        urllib.parse.urljoin(
            EOSC_MARKETPLACE_BASE_URL, OFFER_LIST_URL % (str(eosc_resource_id))
        ),
        headers=headers,
    )
    if response.status_code == http_codes.NOT_FOUND:
        raise Exception(
            f"Could not find offers for resource with ID {eosc_resource_id}"
        )
    data = response.json()
    data = data["offers"]
    offers_names = [item["name"] for item in data]
    offers_ids = [item["id"] for item in data]
    return offers_names, offers_ids


def get_or_create_eosc_resource_offer(
    eosc_resource, waldur_offering
):  # , eosc_marketplace=None
    offers_names, offers_ids = get_all_offers_from_resource(
        eosc_resource_id=eosc_resource["id"]
    )
    offer = sync_offer(
        eosc_resource_id=eosc_resource["id"], waldur_offering=waldur_offering
    )
    if waldur_offering["name"] in offers_names:
        return offer, True
    else:
        return offer, False


def create_offer_for_waldur_offering(waldur_offering, provider_resource):
    eosc_offer, offer_created = get_or_create_eosc_resource_offer(
        provider_resource, waldur_offering
    )
    if offer_created:
        logger.info("New offering has been created in EOSC", eosc_offer)
    else:
        pass
        # TODO: add activation of an offer
    return eosc_offer


def deactivate_offer(waldur_offering):
    # TODO: implement deactivation of an offer
    pass
