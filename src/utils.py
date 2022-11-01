import json
import logging
import os
import sys
import urllib.parse

import requests
from requests.status_codes import codes as http_codes
from waldur_client import WaldurClient

logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def get_env_or_fail(env_variable_name):
    # check that required environment variables is set and exit otherwise
    value = os.environ.get(env_variable_name)
    if not value:
        logger.error(f"Mandatory variable {env_variable_name} is missing or empty.")
        sys.exit(1)
    else:
        return value


EOSC_MARKETPLACE_BASE_URL = get_env_or_fail("EOSC_URL")  # TODO: Fix env var name
EOSC_MARKETPLACE_OFFERING_TOKEN = get_env_or_fail("OFFERING_TOKEN")
EOSC_PROVIDER_PORTAL_BASE_URL = get_env_or_fail("OFFERING_URL")
EOSC_AAI_REFRESH_TOKEN = get_env_or_fail("REFRESH_TOKEN")
EOSC_AAI_CLIENT_ID = get_env_or_fail("CLIENT_ID")
EOSC_AAI_REFRESH_TOKEN_URL = get_env_or_fail("REFRESH_TOKEN_URL")
EOSC_PORTAL_ORGANIZATION_EID = get_env_or_fail("ORGANIZATION_EID")
WALDUR_TOKEN = get_env_or_fail("WALDUR_TOKEN")
WALDUR_API_URL = get_env_or_fail("WALDUR_URL")
WALDUR_TARGET_CUSTOMER_UUID = get_env_or_fail("CUSTOMER_UUID")
CATALOGUE_ID = get_env_or_fail("CATALOGUE_ID")

CATALOGUE_PREFIX = f"/api/catalogue/{CATALOGUE_ID}/"
RESOURCE_LIST_URL = "/api/v1/resources/"
RESOURCE_URL = "/api/v1/resources/%s/"
OFFER_LIST_URL = "/api/v1/resources/%s/offers"
OFFER_URL = "/api/v1/resources/%s/offers/%s"
PROVIDER_SERVICES_URL = CATALOGUE_PREFIX + "%s/resource/all "
PROVIDER_URL = CATALOGUE_PREFIX + "provider/%s"
waldur_client = WaldurClient(WALDUR_API_URL, WALDUR_TOKEN)


def get_provider_token():
    data = {
        "grant_type": "refresh_token",
        "refresh_token": EOSC_AAI_REFRESH_TOKEN,
        "client_id": EOSC_AAI_CLIENT_ID,
        "scope": "openid email profile",
    }

    response = requests.post(EOSC_AAI_REFRESH_TOKEN_URL, data=data)
    response_data = response.json()
    token = response_data["access_token"]
    return token


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
        logging.error(f"Response status code: {response.status_code}")
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
        logging.error("Failed to create an offer.", response.status_code, response.text)
    else:
        offer_data = response.json()
        logging.info(f"Successfully created offer {offer_name} for {eosc_resource_id}.")
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
            logging.info(
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


def create_resource(waldur_offering, provider_contact):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": get_provider_token(),
    }
    landing = (
        WALDUR_API_URL.replace("https://api.", "https://").rstrip("/api/")
        + "/marketplace-public-offering"
        + waldur_offering["uuid"]
        + "/"
    )
    data = {
        "name": waldur_offering["name"],
        "abbreviation": waldur_offering["name"],
        "resourceOrganisation": EOSC_PORTAL_ORGANIZATION_EID,  # waldur_offering['customer_name']
        "resourceProviders": [
            EOSC_PORTAL_ORGANIZATION_EID
        ],  # waldur_offering['customer_name']
        "webpage": landing,
        "description": waldur_offering["description"] or "sample text",
        "tagline": waldur_offering["name"].lower(),
        "logo": waldur_offering["thumbnail"] or "https://etais.ee/images/logo.png",
        "termsOfUse": landing,
        "privacyPolicy": landing,
        "scientificDomains": [
            {
                "scientificDomain": "scientific_domain-agricultural_sciences",
                "scientificSubdomain": "scientific_subdomain-agricultural_sciences-agricultural_biotechnology",
            }
        ],
        # ???
        "categories": [
            {
                "category": "category-aggregators_and_integrators-aggregators_and_integrators",
                "subcategory": "subcategory-aggregators_and_integrators-aggregators_and_integrators-applications",
            }
        ],
        # ???
        "targetUsers": ["target_user-businesses"],
        # "accessTypes": [
        # ],
        # "accessModes": [
        # ],
        # "tags": [
        # ],
        "geographicalAvailabilities": ["EO"],
        "languageAvailabilities": ["en"],
        "mainContact": {
            "firstName": provider_contact["name"],
            "lastName": provider_contact["surname"],
            "email": provider_contact["email"] or "etais@etais.ee",
        },
        "publicContacts": [
            {
                "email": waldur_offering["attributes"]["vpc_Support_email"]
                if len(waldur_offering["attributes"]) > 0
                else "etais@etais.ee",
            }
        ],
        "helpdeskEmail": waldur_offering["attributes"]["vpc_Support_email"]
        if len(waldur_offering["attributes"]) > 0
        else "etais@etais.ee",
        "securityContactEmail": waldur_offering["attributes"]["vpc_Support_email"]
        if len(waldur_offering["attributes"]) > 0
        else "etais@etais.ee",
        "trl": "trl-9",
        "orderType": "order_type-order_required",
    }
    response = requests.post(
        urllib.parse.urljoin(EOSC_PROVIDER_PORTAL_BASE_URL, "resource/"),
        headers=headers,
        data=json.dumps(data),
    )
    if response.status_code not in [200, 201]:
        logging.error(f"Error: {response.text}")
        logging.error(
            "Error creating resource in Marketplace: %s", response.status_code
        )
        sys.exit(1)
    r = response.json()
    return r


def get_resource_by_id(resource_id):
    headers = {"Accept": "application/json"}
    response = requests.get(
        urllib.parse.urljoin(EOSC_PROVIDER_PORTAL_BASE_URL, f"resource/{resource_id}"),
        headers=headers,
    )
    data = response.json()
    return data


def get_all_resources_from_provider():
    headers = {"Accept": "application/json"}
    response = requests.get(
        urllib.parse.urljoin(
            EOSC_PROVIDER_PORTAL_BASE_URL,
            PROVIDER_SERVICES_URL % EOSC_PORTAL_ORGANIZATION_EID,
        ),
        # 'provider/services/tnp'
        headers=headers,
    )
    data = response.json()
    resource_names = [item["name"] for item in data]
    resource_ids = [item["id"] for item in data]
    return resource_names, resource_ids


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


def get_or_create_eosc_resource(
    waldur_offering, provider_contact
):  # , eosc_provider_portal=None
    resource_names, resource_ids = get_all_resources_from_provider()
    if waldur_offering["name"] in resource_names:
        existing_resource = get_resource_by_id(
            resource_ids[resource_names.index(waldur_offering["name"])]
        )
        logging.info(f'Resource is already in EOSC: {existing_resource["name"]}')
        return existing_resource, False
    else:
        resource = create_resource(waldur_offering, provider_contact)
        return resource, True


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


def get_or_create_eosc_provider(waldur_customer_uuid):
    provider = {}
    try:
        headers = {
            "Accept": "application/json",
            "Authorization": get_provider_token(),
        }
        response = requests.get(
            urllib.parse.urljoin(
                EOSC_PROVIDER_PORTAL_BASE_URL,
                PROVIDER_URL % EOSC_PORTAL_ORGANIZATION_EID,
            ),
            headers=headers,
        )

        if response.status_code == http_codes.NOT_FOUND:
            # TODO: add creation of a provider
            pass

        provider = response.json()
        provider_contact = provider["users"][-1]
    except ValueError:
        return provider, False, None
    else:
        logging.info(f'Existing provider name: {provider["name"]}')
        provider["is_approved"] = True
        return provider, False, provider_contact


def create_offer_for_waldur_offering(waldur_offering, provider_contact):
    eosc_resource, eosc_resource_created = get_or_create_eosc_resource(
        waldur_offering, provider_contact
    )
    if eosc_resource_created:
        logging.info("New resource has been created in EOSC", eosc_resource)
    eosc_resource_offers, offer_created = get_or_create_eosc_resource_offer(
        eosc_resource, waldur_offering
    )
    if offer_created:
        logging.info("New offering has been created in EOSC", eosc_resource)
    else:
        pass
        # TODO: add activation of an offer


def deactivate_offer(waldur_offering):
    # TODO: implement deactivation of an offer
    pass


def process_offers():
    waldur_offerings = waldur_client.list_marketplace_offerings(
        {
            "customer_uuid": WALDUR_TARGET_CUSTOMER_UUID,
            "attributes": '{"enable_sync_to_eosc":true}',
        },
    )

    for waldur_offering in waldur_offerings:
        try:
            provider, created, provider_contact = get_or_create_eosc_provider(
                waldur_offering["customer_uuid"]
            )
            if created:
                logging.info("Provider has been created, pending approval")
            if provider["is_approved"]:
                if waldur_offering["state"] in ["Active", "Paused"]:
                    create_offer_for_waldur_offering(waldur_offering, provider_contact)
                elif waldur_offering["state"] in ["Archived", "Draft"]:
                    deactivate_offer(waldur_offering)
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
