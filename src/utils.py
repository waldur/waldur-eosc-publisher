import json
import logging
import os
import urllib.parse

import requests
from waldur_client import WaldurClient

logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

EOSC_URL = os.environ.get("EOSC_URL")  # polling url
OFFERING_URL = os.environ.get("OFFERING_URL")
WALDUR_TOKEN = os.environ.get("WALDUR_TOKEN")
OFFERING_TOKEN = os.environ.get("OFFERING_TOKEN")
REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN")
CLIENT_ID = os.environ.get("CLIENT_ID")
REFRESH_TOKEN_URL = os.environ.get("REFRESH_TOKEN_URL")
WALDUR_API_URL = os.environ.get("WALDUR_URL")
CUSTOMER_UUID = os.environ.get("CUSTOMER_UUID")
ORGANIZATION_EID = os.environ.get("ORGANIZATION_EID")

RESOURCE_LIST_URL = "/api/v1/resources/"
RESOURCE_URL = "/api/v1/resources/%s/"
OFFER_LIST_URL = "/api/v1/resources/%s/offers"
OFFER_URL = "/api/v1/resources/%s/offers/%s"
PROVIDER_SERVICES_URL = "provider/services/%s"
PROVIDER_URL = "provider/%s"


def get_waldur_client():
    waldur_client = WaldurClient(WALDUR_API_URL, WALDUR_TOKEN)
    return waldur_client


def get_provider_token():
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "scope": "openid email profile",
    }

    response = requests.post(REFRESH_TOKEN_URL, data=data)
    response_data = response.json()
    token = response_data["access_token"]
    return token


def resource_and_offering_request():
    headers = {
        "accept": "application/json",
        "X-User-Token": OFFERING_TOKEN,
    }
    return headers


def offering_request_post_patch(
    offer_name: str, offer_description: str, offer_parameters, internal=True
):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-User-Token": OFFERING_TOKEN,
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
        "X-User-Token": OFFERING_TOKEN,
    }
    return headers


def get_resource_list():
    headers = resource_and_offering_request()
    response = requests.get(
        urllib.parse.urljoin(EOSC_URL, RESOURCE_LIST_URL), headers=headers
    )
    resource_list_data = response.json()
    return resource_list_data


def get_resource(resource_id):
    headers = resource_and_offering_request()
    response = requests.get(
        urllib.parse.urljoin(EOSC_URL, RESOURCE_URL % (str(resource_id))),
        headers=headers,
    )
    resource_data = response.json()
    return resource_data


def get_offer_list_of_resource(resource_id):
    headers = resource_and_offering_request()
    response = requests.get(
        urllib.parse.urljoin(EOSC_URL, OFFER_LIST_URL % (str(resource_id))),
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
        "X-User-Token": OFFERING_TOKEN,
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
        urllib.parse.urljoin(EOSC_URL, OFFER_LIST_URL % eosc_resource_id),
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
        urllib.parse.urljoin(EOSC_URL, OFFER_URL % (str(resource_id), str(offer_id))),
        headers=headers,
        data=data,
    )
    patch_offer_data = response.json()
    return patch_offer_data


def delete_offer_from_resource(resource_id, offer_id):
    headers = offering_request_delete()
    response = requests.delete(
        urllib.parse.urljoin(EOSC_URL, OFFER_URL % (str(resource_id), str(offer_id))),
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


def sync_offer(eosc_resource_id, waldur_resource):
    eosc_offers = get_offer_list_of_resource(eosc_resource_id)["offers"]
    eosc_offers_names = {offer["name"] for offer in eosc_offers}
    for plan in waldur_resource["plans"]:
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
        for component in waldur_resource["components"]:
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
                        f"{waldur_resource['name']}.",
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


def create_resource(waldur_resource, provider_contact):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": get_provider_token(),
    }
    data = {
        "name": waldur_resource["name"],
        "resourceOrganisation": ORGANIZATION_EID,  # waldur_offering['customer_name']
        "resourceProviders": [ORGANIZATION_EID],  # waldur_offering['customer_name']
        "webpage": WALDUR_API_URL.replace(
            "https://api.", "https://"
        ),  # waldur_offering['url'] , "https://example.com"
        "description": waldur_resource["description"] or "sample text",
        "tagline": waldur_resource["name"].lower(),
        "logo": waldur_resource["thumbnail"] or "https://etais.ee/images/logo.png",
        # ???
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
                "email": waldur_resource["attributes"]["vpc_Support_email"]
                if len(waldur_resource["attributes"]) > 0
                else "etais@etais.ee",
            }
        ],
        "helpdeskEmail": waldur_resource["attributes"]["vpc_Support_email"]
        if len(waldur_resource["attributes"]) > 0
        else "etais@etais.ee",
        "securityContactEmail": waldur_resource["attributes"]["vpc_Support_email"]
        if len(waldur_resource["attributes"]) > 0
        else "etais@etais.ee",
        "trl": "trl-1",
        "orderType": "order_type-order_required",
    }
    response = requests.post(
        urllib.parse.urljoin(OFFERING_URL, "resource/"),
        headers=headers,
        data=json.dumps(data),
    )
    if response.status_code == 409:
        logging.error(f"Error: {response.text}")
    r = response.json()
    return r, response.status_code


def get_resource_by_id(resource_id):
    headers = {"Accept": "application/json"}
    response = requests.get(
        urllib.parse.urljoin(OFFERING_URL, f"resource/{resource_id}"), headers=headers
    )
    data = response.json()
    return data


def get_all_resources_from_provider():
    headers = {"Accept": "application/json"}
    response = requests.get(
        urllib.parse.urljoin(OFFERING_URL, PROVIDER_SERVICES_URL % ORGANIZATION_EID),
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
        "X-User-Token": OFFERING_TOKEN,
    }
    response = requests.get(
        urllib.parse.urljoin(EOSC_URL, OFFER_LIST_URL % (str(eosc_resource_id))),
        headers=headers,
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
        resource, status_code = create_resource(waldur_offering, provider_contact)
        if status_code == 409:
            return resource, False
        return resource, True


def get_or_create_eosc_resource_offer(
    eosc_resource, waldur_resource
):  # , eosc_marketplace=None
    offers_names, offers_ids = get_all_offers_from_resource(
        eosc_resource_id=eosc_resource["id"]
    )
    offer = sync_offer(
        eosc_resource_id=eosc_resource["id"], waldur_resource=waldur_resource
    )
    if waldur_resource["name"] in offers_names:
        return offer, True
    else:
        return offer, False


def get_or_create_eosc_provider(customer=None):  # only get atm
    provider = {}
    try:
        headers = {
            "Accept": "application/json",
            "Authorization": get_provider_token(),
        }
        # tnp - test nordic provider
        response = requests.get(
            urllib.parse.urljoin(OFFERING_URL, PROVIDER_URL % ORGANIZATION_EID),
            headers=headers,
        )
        provider = response.json()
        provider_contact = provider["users"][-1]
    except ValueError:
        return provider, False
    else:
        logging.info(f'Existing provider name: {provider["name"]}')
        provider["is_approved"] = True
        return provider, False, provider_contact


def get_waldur_offerings():
    list_resources = get_waldur_client().list_marketplace_offerings(
        {"customer_uuid": CUSTOMER_UUID}
    )
    return list_resources


def process_offers():
    waldur_offerings = get_waldur_offerings()

    for waldur_offering in waldur_offerings:
        try:
            provider, created, provider_contact = get_or_create_eosc_provider(
                waldur_offering["customer"]
            )
            if created:
                logging.info("Provider has been created, pending approval")
            if provider["is_approved"]:
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
