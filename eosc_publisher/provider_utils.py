import json.decoder
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
    logger,
    waldur_client,
)

DEFAULT_SUPPORT_EMAIL = "support@puhuri.io"


def construct_abbreviation(name):
    name_split = name.split()
    if len(name_split) > 1:
        return "".join(w[0].upper() for w in name.split() if w[0].isalnum())
    else:
        return name.upper()


def get_provider_token():
    data = {
        "grant_type": "refresh_token",
        "refresh_token": EOSC_AAI_REFRESH_TOKEN,
        "client_id": EOSC_AAI_CLIENT_ID,
        "scope": "openid email profile",
    }

    response = requests.post(EOSC_AAI_REFRESH_TOKEN_URL, data=data)
    if response.status_code != 200:
        logger.error(
            f"Failed to get access token, {response.status_code}. {response.text}"
        )
        return None
    response_data = response.json()
    token = response_data["access_token"]
    return token


def construct_provider_payload(waldur_customer, provider_id=None, users=[]):
    if waldur_customer["image"]:
        logo_url = waldur_customer["image"]
    else:
        configuration = waldur_client.get_configuration()
        homeport_url = configuration["WALDUR_CORE"]["HOMEPORT_URL"]
        logo_url = urllib.parse.urljoin(
            homeport_url,
            "images/login_logo.png",
        )

    address_split = waldur_customer["address"].split(maxsplit=1)
    if address_split:
        [city, address] = address_split
    else:
        [city, address] = ["unknown", "unknown"]

    service_provider = waldur_client.list_service_providers(
        filters={"customer_uuid": waldur_customer["uuid"]}
    )[0]
    description = (
        service_provider["description"]
        or "%s provider in EOSC portal" % waldur_customer["name"]
    )
    abbreviation = waldur_customer["abbreviation"] or construct_abbreviation(
        waldur_customer["name"]
    )
    provider_payload = {
        "abbreviation": abbreviation,
        "name": waldur_customer["name"],
        "website": waldur_customer["homepage"] or "https://share.neic.no/",
        "legalEntity": True,
        "legalStatus": "provider_legal_status-public_legal_entity",
        "description": description,
        "logo": logo_url,
        "location": {
            "streetNameAndNumber": address,
            "postalCode": waldur_customer["postal"] or "00000",
            "city": city,
            "country": waldur_customer["country"] or "OT",
        },
        "participatingCountries": [waldur_customer["country"]],
        "catalogueId": EOSC_CATALOGUE_ID,
        "users": users,
    }
    if provider_id:
        provider_payload["id"] = provider_id

    provider_payload["mainContact"] = {
        "firstName": "-",
        "lastName": "-",
        "email": DEFAULT_SUPPORT_EMAIL,
    }
    provider_payload["publicContacts"] = [
        {"email": waldur_customer["email"] or DEFAULT_SUPPORT_EMAIL}
    ]

    if waldur_customer["division"]:
        provider_payload["affiliations"] = [waldur_customer["division"]]

    return provider_payload


def construct_resource_payload(waldur_offering, provider_id, resource_id=None):
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

    # TODO: before fixing abbreviation construction,
    # add ID of a resource to waldur offering options and
    # use the value from options for lookup instead of name
    abbreviation = construct_abbreviation(waldur_offering["name"])

    resource_payload = {
        "abbreviation": abbreviation,
        "accessModes": ["access_mode-other"],
        "accessTypes": ["access_type-remote", "access_type-virtual"],
        "accessPolicy": None,
        "catalogueId": EOSC_CATALOGUE_ID,
        "categories": [
            {
                "category": "category-aggregators_and_integrators-aggregators_and_integrators",
                "subcategory": "subcategory-aggregators_and_integrators-aggregators_and_integrators-applications",
            }
        ],
        "certifications": [],
        "changeLog": [],
        "description": waldur_offering["description"] or "None",
        "fundingBody": [],
        "fundingPrograms": [],
        "geographicalAvailabilities": ["EO", "WW"],
        "grantProjectNames": [],
        "helpdeskEmail": helpdesk_email,
        "helpdeskPage": "",  # https://puhuri.neic.no/
        "languageAvailabilities": ["en"],
        "lastUpdate": None,
        "lifeCycleStatus": None,
        "logo": logo_url,
        "mainContact": {
            "firstName": "-",
            "lastName": "-",
            "email": DEFAULT_SUPPORT_EMAIL,
        },
        "maintenance": None,
        "multimedia": [],
        "name": waldur_offering["name"],
        "openSourceTechnologies": [],
        "order": landing,
        "orderType": "order_type-order_required",
        "paymentModel": None,
        "pricing": None,
        "privacyPolicy": waldur_offering["privacy_policy_link"]
        or "https://placeholder.example.com",
        "publicContacts": [
            {
                "email": public_email,
                "firstName": None,
                "lastName": None,
                "organisation": None,
                "phone": "",
                "position": None,
            }
        ],
        "relatedPlatforms": [],
        "relatedResources": [],
        "requiredResources": [],
        "resourceGeographicLocations": [],
        "resourceLevel": None,
        "resourceOrganisation": provider_id,
        "resourceProviders": [provider_id],
        "scientificDomains": [
            {
                "scientificDomain": "scientific_domain-generic",
                "scientificSubdomain": "scientific_subdomain-generic-generic",
            }
        ],
        "securityContactEmail": security_email,
        "standards": [],
        "statusMonitoring": None,
        "tagline": waldur_offering["name"].lower(),
        "tags": [
            "data-access",
            "remote-access",
            "collaboration",
        ],
        "targetUsers": ["target_user-researchers"],
        "termsOfUse": waldur_offering["terms_of_service_link"]
        or "https://placeholder.example.com",
        "trainingInformation": None,
        "trl": "trl-9",
        "useCases": [],
        "userManual": "",
        "version": None,
        "webpage": landing,
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
        urllib.parse.urljoin(
            EOSC_PROVIDER_PORTAL_BASE_URL, PROVIDER_RESOURCE_URL + resource_id
        ),
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
            CATALOGUE_SERVICES_URL,
        ),
        headers=headers,
        params={"catalogue_id": EOSC_CATALOGUE_ID, "quantity": 1000},
    )
    if response.status_code != 200:
        logger.error(
            f"Failed to get list of resources with code {response.status_code}. Message: {response.text}"
        )
        return []
    data = response.json()
    resource_list = data["results"]
    resource_names_and_ids = {
        resource["name"]: resource["id"] for resource in resource_list
    }
    return resource_names_and_ids


def fetch_all_resources_from_eosc_catalogue():
    token = get_provider_token()
    if token:
        return get_all_resources_from_catalogue(token)
    else:
        return None


def update_resource(waldur_offering, provider_id, resource_id, token):
    logger.info("Updating resource %s for provider %s", resource_id, provider_id)
    headers = {
        "Authorization": token,
    }
    resource_payload = construct_resource_payload(
        waldur_offering, provider_id, resource_id
    )
    response = requests.put(
        urllib.parse.urljoin(EOSC_PROVIDER_PORTAL_BASE_URL, PROVIDER_RESOURCE_URL),
        headers=headers,
        json=resource_payload,
    )
    if response.status_code not in [200, 201]:
        logger.warning(
            "Error during updating of resource in the provider portal. Code %s, error: %s",
            response.status_code,
            response.text,
        )
    else:
        try:
            resource = response.json()
        except json.JSONDecodeError as err:
            if "There are no changes in the Service" in response.text:
                return
            logger.error("Error parsing %s", response.text)
            logger.exception(err)
            return

        logger.info(
            "The resource %s has been successfully updated",
            resource["name"],
        )
        return resource


def create_resource(waldur_offering, provider_id, token):
    logger.info(
        "Creating a resource %s for provider %s",
        waldur_offering["name"],
        provider_id,
    )
    headers = {
        "Authorization": token,
    }
    resource_payload = construct_resource_payload(waldur_offering, provider_id)
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


def delete_resource(resource_id, token):
    logger.info("Deleting the resource %s", resource_id)
    headers = {
        "Authorization": token,
    }

    url = (
        urllib.parse.urljoin(EOSC_PROVIDER_PORTAL_BASE_URL, PROVIDER_RESOURCE_URL)
        + resource_id
    )
    response = requests.delete(url, headers=headers)

    if response.status_code not in [http_codes.OK, http_codes.NO_CONTENT]:
        logger.error(
            "Unable to delete resource. Code: %s, details: %s",
            response.status_code,
            response.text,
        )
        return

    logger.info("The resource has been successfully removed from the catalogue")
    deleted_resource = response.json()
    return deleted_resource


def create_eosc_resource(waldur_offering, provider_id):
    logger.info("The resource is missing, creating a new one.")
    token = get_provider_token()
    resource = create_resource(waldur_offering, provider_id, token)
    return resource


def update_eosc_resource(waldur_offering, provider_id, resource_id):
    logger.info("Resource already exists in EOSC: %s", waldur_offering["name"])
    token = get_provider_token()
    existing_resource = get_resource_by_id(resource_id, token)
    updated_existing_resource = update_resource(
        waldur_offering, provider_id, resource_id, token
    )
    return updated_existing_resource or existing_resource


def delete_eosc_resource(resource_id):
    token = get_provider_token()
    logger.info("Resource %s is found, removing it from the portal", resource_id)
    deleted_resource = delete_resource(resource_id, token)
    return deleted_resource


def update_provider(waldur_customer, provider_id, token, users):
    logger.info("Updating the provider")
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
        logger.warning(
            "Unable to update the provider (id=%s). Code %s, error: %s",
            provider_id,
            provider_response.status_code,
            provider_response.text,
        )
        return

    try:
        provider = provider_response.json()
        logger.info("The provider %s has been successfully updated", provider["name"])
        return provider
    except json.decoder.JSONDecodeError:
        logger.info(
            f"Didn't update: {provider_response.status_code}, {provider_response.text}"
        )
        # Provider portal return XML wtih error message and 200 response code if entry hasn't been updated
        return None


def create_provider(waldur_customer, token):
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


def get_provider(provider_id, token):
    logger.info("Fetching provider [id=%s] data.", provider_id)
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
        "Unable to get a provider. Code %s, error: %s"
        % (provider_response.status_code, provider_response.text)
    )


def get_eosc_provider(waldur_customer):
    provider_id = (
        waldur_customer["abbreviation"]
        or construct_abbreviation(waldur_customer["name"])
    ).lower()

    token = get_provider_token()

    provider = get_provider(provider_id, token)
    return provider


def sync_eosc_provider(waldur_customer, existing_provider):
    provider_id = (
        waldur_customer["abbreviation"]
        or construct_abbreviation(waldur_customer["name"])
    ).lower()

    logger.info(
        "Syncing customer %s (provider %s)", waldur_customer["name"], provider_id
    )

    token = get_provider_token()
    # TODO: add customer deletion
    if existing_provider is None:
        created_provider = create_provider(waldur_customer, token)
        return created_provider
    else:
        refreshed_provider_json = update_provider(
            waldur_customer, existing_provider["id"], token, existing_provider["users"]
        )
        return refreshed_provider_json or existing_provider
