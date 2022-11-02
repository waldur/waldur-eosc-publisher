import urllib.parse

import requests
from requests.status_codes import codes as http_codes

from . import (
    EOSC_AAI_CLIENT_ID,
    EOSC_AAI_REFRESH_TOKEN,
    EOSC_AAI_REFRESH_TOKEN_URL,
    EOSC_CATALOGUE_ID,
    EOSC_PORTAL_ORGANIZATION_EID,
    EOSC_PROVIDER_PORTAL_BASE_URL,
    PROVIDER_SERVICES_URL,
    PROVIDER_URL,
    WALDUR_API_URL,
    WALDUR_TARGET_CUSTOMER_UUID,
    logger,
    waldur_client,
)


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
        # 'catalogue/<eosc-nordic>/<tnp>/resource/all'
        headers=headers,
    )
    data = response.json()
    resource_names = [item["name"] for item in data]
    resource_ids = [item["id"] for item in data]
    return resource_names, resource_ids


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
    resource_payload = {
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
        "catalogueId": EOSC_CATALOGUE_ID,
        "orderType": "order_type-order_required",
    }
    response = requests.post(
        urllib.parse.urljoin(EOSC_PROVIDER_PORTAL_BASE_URL, "resource/"),
        headers=headers,
        data=resource_payload,
    )
    if response.status_code not in [200, 201]:
        logger.error(
            "Error creating resource in Marketplace. Code %s, error: %s",
            (response.status_code, response.text),
        )
    else:
        return response.json()


def get_or_create_eosc_resource(
    waldur_offering, provider_contact
):  # , eosc_provider_portal=None
    resource_names, resource_ids = get_all_resources_from_provider()
    if waldur_offering["name"] in resource_names:
        existing_resource = get_resource_by_id(
            resource_ids[resource_names.index(waldur_offering["name"])]
        )
        logger.info("Resource is already in EOSC: %s", existing_resource["name"])
        return existing_resource
    else:
        resource = create_resource(waldur_offering, provider_contact)
        logger.info("New resource has been created in EOSC: %s", resource)
        return resource


def create_eosc_provider():
    waldur_customer = waldur_client._get_resource(
        waldur_client.Endpoints.Customers, WALDUR_TARGET_CUSTOMER_UUID
    )

    if waldur_customer["image"]:
        logo_url = waldur_customer["homepage"]
    else:
        configuration = waldur_client.get_configuration()
        homeport_url = configuration["WALDUR_CORE"]["HOMEPORT_URL"]
        logo_url = urllib.parse.urljoin(
            homeport_url,
            "images/login_logo.png",
        )

    [city, address] = waldur_customer["address"].split(maxsplit=1)

    service_provider = waldur_client.list_service_providers(
        filters={"customer_uuid": WALDUR_TARGET_CUSTOMER_UUID}
    )[0]
    description = (
        service_provider["description"]
        or "%s provider in EOSC marketplace" % waldur_customer["name"]
    )
    provider_payload = {
        "abbreviation": waldur_customer["abbreviation"],
        "name": waldur_customer["name"],
        "website": waldur_customer["homepage"],
        "legalEntity": False,
        "description": description,
        "logo": logo_url,
        "location": {
            "streetNameAndNumber": address,
            "postalCode": waldur_customer["postal"],
            "city": city,
            "country": waldur_customer["country"],
        },
        "participatingCountries": [waldur_customer["country"]],
        "catalogueId": EOSC_CATALOGUE_ID,
        "users": [],
    }

    first_owner = waldur_customer["owners"][0]
    [first_name, last_name] = first_owner["full_name"].split(maxsplit=1)
    provider_payload["mainContact"] = {
        "firstName": first_name,
        "lastName": last_name,
        "email": first_owner["email"],
        "phone": waldur_customer["phone_number"],
    }
    provider_payload["publicContacts"] = [
        {"email": waldur_customer["email"] or first_owner["email"]}
    ]

    if waldur_customer["domain"]:
        provider_payload["scientificDomains"] = [
            {
                "scientificDomain": waldur_customer["domain"],
                "scientificSubdomain": waldur_customer["domain"],
            }
        ]

    if waldur_customer["division"]:
        provider_payload["affiliations"] = [waldur_customer["division"]]

    provider_url = urllib.parse.urljoin(
        EOSC_PROVIDER_PORTAL_BASE_URL,
        PROVIDER_URL,
    )
    provider_response = requests.post(
        provider_url,
        data=provider_payload,
    )

    if provider_response.status_code not in [http_codes.OK, http_codes.CREATED]:
        raise Exception(
            "Unable to create a new provider. Code %s, error: %s"
            % (provider_response.status_code, provider_response.text)
        )

    return provider_response.json()


def get_or_create_eosc_provider():
    headers = {
        "Accept": "application/json",
        "Authorization": get_provider_token(),
    }
    provider_url = urllib.parse.urljoin(
        EOSC_PROVIDER_PORTAL_BASE_URL,
        f"{PROVIDER_URL}/{EOSC_PORTAL_ORGANIZATION_EID}",
    )
    provider_response = requests.get(
        provider_url,
        headers=headers,
    )

    if provider_response.status_code == http_codes.NOT_FOUND:
        provider_json = create_eosc_provider()
        return provider_json, True
    elif provider_response.status_code == http_codes.OK:
        provider_json = provider_response.json()
        logger.info("Existing provider name: %s", provider_json["name"])
        provider_json["is_approved"] = True
        return provider_json, False
    else:
        raise Exception(
            "Unable to get a provider. Code %s, error: %",
            (provider_response.status_code, provider_response.text),
        )
