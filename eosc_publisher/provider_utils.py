import urllib.parse

import requests
from requests.status_codes import codes as http_codes

from . import (
    CATALOGUE_SERVICES_URL,
    EOSC_AAI_CLIENT_ID,
    EOSC_AAI_REFRESH_TOKEN,
    EOSC_AAI_REFRESH_TOKEN_URL,
    EOSC_CATALOGUE_ID,
    EOSC_PROVIDER_PORTAL_BASE_URL,
    PROVIDER_RESOURCE_URL,
    PROVIDER_URL,
    WALDUR_TARGET_CUSTOMER_UUID,
    logger,
    waldur_client,
)

DEFAULT_SUPPORT_EMAIL = "support@puhuri.io"


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


def construct_provider_payload(waldur_customer, provider_id=None, users=[]):
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
        or "%s provider in EOSC portal" % waldur_customer["name"]
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
        "users": users,
    }
    if provider_id:
        provider_payload["id"] = provider_id

    first_owner = waldur_customer["owners"][0]
    [first_name, last_name] = first_owner["full_name"].split(maxsplit=1)
    provider_payload["mainContact"] = {
        "firstName": first_name,
        "lastName": last_name,
        "email": first_owner["email"],
        "phone": waldur_customer["phone_number"],
    }
    provider_payload["publicContacts"] = [
        {"email": waldur_customer["email"] or DEFAULT_SUPPORT_EMAIL}
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

    return provider_payload


def construct_resource_payload(
    waldur_offering, provider_contact, provider_id, resource_id=None
):
    configuration = waldur_client.get_configuration()
    homeport_url = configuration["WALDUR_CORE"]["HOMEPORT_URL"]
    landing = urllib.parse.urljoin(
        homeport_url,
        f"marketplace-public-offering/{waldur_offering['uuid']}/",
    )
    helpdesk_email = (
        waldur_offering["attributes"]["vpc_Support_email"]
        if waldur_offering["attributes"].get("vpc_Support_email")
        else DEFAULT_SUPPORT_EMAIL
    )
    public_email = (
        waldur_offering["attributes"]["vpc_Support_email"]
        if waldur_offering["attributes"].get("vpc_Support_email")
        else DEFAULT_SUPPORT_EMAIL
    )
    security_email = (
        waldur_offering["attributes"]["vpc_Support_email"]
        if waldur_offering["attributes"].get("vpc_Support_email")
        else DEFAULT_SUPPORT_EMAIL
    )
    if waldur_offering["thumbnail"]:
        logo_url = waldur_offering["thumbnail"]
    else:
        configuration = waldur_client.get_configuration()
        homeport_url = configuration["WALDUR_CORE"]["HOMEPORT_URL"]
        logo_url = urllib.parse.urljoin(
            homeport_url,
            "images/login_logo.png",
        )
    resource_payload = {
        "name": waldur_offering["name"],
        "abbreviation": waldur_offering["name"],
        "resourceOrganisation": provider_id,
        "resourceProviders": [provider_id],
        "webpage": landing,
        "description": waldur_offering["description"] or "sample text",
        "tagline": waldur_offering["name"].lower(),
        "logo": logo_url,
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
        "geographicalAvailabilities": ["EO"],
        "languageAvailabilities": ["en"],
        "mainContact": {
            "firstName": provider_contact["name"],
            "lastName": provider_contact["surname"],
            "email": provider_contact["email"] or DEFAULT_SUPPORT_EMAIL,
        },
        "publicContacts": [
            {
                "email": public_email,
            }
        ],
        "helpdeskEmail": helpdesk_email,
        "securityContactEmail": security_email,
        "trl": "trl-9",
        "catalogueId": EOSC_CATALOGUE_ID,
        "orderType": "order_type-order_required",
    }

    if resource_id:
        resource_payload["id"] = resource_id

    return resource_payload


def get_resource_by_id(resource_id, token):
    headers = {
        "Accept": "application/json",
        "Authorization": token,
    }
    response = requests.get(
        urllib.parse.urljoin(EOSC_PROVIDER_PORTAL_BASE_URL, f"resource/{resource_id}"),
        headers=headers,
    )
    data = response.json()
    return data


def get_all_resources_from_catalogue(token):
    logger.info("Fetching all resources for catalogue %s", EOSC_CATALOGUE_ID)
    headers = {
        "Accept": "application/json",
        "Authorization": token,
    }
    response = requests.get(
        urllib.parse.urljoin(
            EOSC_PROVIDER_PORTAL_BASE_URL,
            f"{CATALOGUE_SERVICES_URL}{EOSC_CATALOGUE_ID}",
        ),
        headers=headers,
    )
    data = response.json()
    resource_list = data["results"]
    resource_names_and_ids = {
        resource["name"]: resource["id"] for resource in resource_list
    }
    return resource_names_and_ids


def update_eosc_resource(
    waldur_offering, provider_contact, provider_id, resource_id, token
):
    logger.error("Updating resource %s for provider %s", resource_id, provider_id)
    headers = {
        "Authorization": token,
    }
    resource_payload = construct_resource_payload(
        waldur_offering, provider_contact, provider_id, resource_id
    )
    response = requests.put(
        urllib.parse.urljoin(EOSC_PROVIDER_PORTAL_BASE_URL, PROVIDER_RESOURCE_URL),
        headers=headers,
        json=resource_payload,
    )
    if response.status_code not in [200, 201]:
        logger.error(
            "Error during updating of resource in the provider portal. Code %s, error: %s",
            response.status_code,
            response.text,
        )
    else:
        resource = response.json()
        logger.info(
            "The resource %s has been successfully updated",
            resource["name"],
        )
        return resource


def create_eosc_resource(waldur_offering, provider_contact, provider_id, token):
    logger.info(
        "Creating a resource %s for provider %s",
        waldur_offering["name"],
        provider_id,
    )
    headers = {
        "Authorization": token,
    }
    resource_payload = construct_resource_payload(
        waldur_offering, provider_contact, provider_id
    )
    response = requests.post(
        urllib.parse.urljoin(EOSC_PROVIDER_PORTAL_BASE_URL, PROVIDER_RESOURCE_URL),
        headers=headers,
        json=resource_payload,
    )
    if response.status_code not in [200, 201]:
        raise Exception(
            "Error creating resource in Providers portal. Code %s, error: %s"
            % (response.status_code, response.text),
        )
    else:
        logger.info(
            "The resource %s has been successfully created", waldur_offering["name"]
        )
        return response.json()


def sync_eosc_resource(
    waldur_offering, provider_contact, provider_id
):  # , eosc_provider_portal=None
    logger.info("Syncing resource for offering %s", waldur_offering["name"])
    token = get_provider_token()
    resource_names_and_ids = get_all_resources_from_catalogue(token)
    if waldur_offering["name"] in resource_names_and_ids:
        resource_id = resource_names_and_ids[waldur_offering["name"]]
        existing_resource = get_resource_by_id(resource_id, token)
        logger.info("Resource already exists in EOSC: %s", existing_resource["name"])
        updated_existing_resource = update_eosc_resource(
            waldur_offering, provider_contact, provider_id, resource_id, token
        )
        return updated_existing_resource
    else:
        logger.info("The resource is missing, creating a new one")
        resource = create_eosc_resource(
            waldur_offering, provider_contact, provider_id, token
        )
        return resource


def update_eosc_provider(waldur_customer, provider_id, token, users):
    provider_payload = construct_provider_payload(waldur_customer, provider_id, users)

    provider_url = urllib.parse.urljoin(
        EOSC_PROVIDER_PORTAL_BASE_URL,
        PROVIDER_URL,
    )
    headers = {
        "Authorization": token,
    }
    provider_response = requests.put(
        provider_url, json=provider_payload, headers=headers
    )

    if provider_response.status_code not in [http_codes.OK, http_codes.CREATED]:
        raise Exception(
            "Unable to update the provider (id=%s). Code %s, error: %s"
            % (provider_id, provider_response.status_code, provider_response.text)
        )

    provider = provider_response.json()
    logger.info("The provider %s has been successfully updated", provider["name"])
    return provider


def create_eosc_provider(waldur_customer, token):
    logger.info("Creating a provider for customer %s", waldur_customer["name"])
    provider_payload = construct_provider_payload(waldur_customer)

    provider_url = urllib.parse.urljoin(
        EOSC_PROVIDER_PORTAL_BASE_URL,
        PROVIDER_URL,
    )
    headers = {
        "Authorization": token,
    }
    provider_response = requests.post(
        provider_url,
        json=provider_payload,
        headers=headers,
    )

    if provider_response.status_code not in [http_codes.OK, http_codes.CREATED]:
        raise Exception(
            "Unable to create a new provider. Code %s, error: %s"
            % (provider_response.status_code, provider_response.text)
        )

    provider = provider_response.json()
    logger.info("The provider %s has been successfully created", provider["name"])
    return provider


def get_eosc_provider(provider_id, token):
    headers = {
        "Accept": "application/json",
        "Authorization": token,
    }
    provider_url = urllib.parse.urljoin(
        EOSC_PROVIDER_PORTAL_BASE_URL,
        f"{PROVIDER_URL}{provider_id}",
    )
    provider_response = requests.get(
        provider_url,
        headers=headers,
    )

    if provider_response.status_code == http_codes.NOT_FOUND:
        logger.info("The provider is not found")
        return

    if provider_response.status_code == http_codes.OK:
        provider_json = provider_response.json()
        logger.info("Existing provider name: %s", provider_json["name"])
        return provider_json

    raise Exception(
        "Unable to sync a provider. Code %s, error: %s"
        % (provider_response.status_code, provider_response.text)
    )


def sync_eosc_provider():
    waldur_customer = waldur_client._get_resource(
        waldur_client.Endpoints.Customers, WALDUR_TARGET_CUSTOMER_UUID
    )
    provider_id = waldur_customer["abbreviation"].lower()
    if not provider_id:
        logger.error("The customer %s does not have abbreviation, skipping it")
        return
    logger.info(
        "Syncing customer %s (provider %s)", waldur_customer["name"], provider_id
    )

    token = get_provider_token()
    existing_provider = get_eosc_provider(provider_id, token)

    if existing_provider is None:
        created_provider = create_eosc_provider(waldur_customer, token)
        return created_provider
    else:
        refreshed_provider_json = update_eosc_provider(
            waldur_customer, existing_provider["id"], token, existing_provider["users"]
        )
        return refreshed_provider_json
