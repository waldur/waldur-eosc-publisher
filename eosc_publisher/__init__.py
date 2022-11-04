import logging
import os
import sys

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
EOSC_CATALOGUE_ID = get_env_or_fail("EOSC_CATALOGUE_ID")
WALDUR_TOKEN = get_env_or_fail("WALDUR_TOKEN")
WALDUR_API_URL = get_env_or_fail("WALDUR_URL")
WALDUR_TARGET_CUSTOMER_UUID = get_env_or_fail("CUSTOMER_UUID")

CATALOGUE_PREFIX = f"/api/catalogue/{EOSC_CATALOGUE_ID}/"
MARKETPLACE_RESOURCE_LIST_URL = "/api/v1/resources/"
MARKETPLACE_RESOURCE_URL = "/api/v1/resources/%s/"
OFFER_LIST_URL = "/api/v1/resources/%s/offers/"
OFFER_URL = "/api/v1/resources/%s/offers/%s"
PROVIDER_SERVICES_URL = CATALOGUE_PREFIX + "%s/resource/all"
PROVIDER_RESOURCE_URL = "resource/"
CATALOGUE_SERVICES_URL = "service/byCatalogue"
PROVIDER_URL = CATALOGUE_PREFIX + "provider/"
waldur_client = WaldurClient(WALDUR_API_URL, WALDUR_TOKEN)


scientific_domain_and_subdomain_dict = {
    "scientific_domain-agricultural_sciences": [
        "scientific_subdomain-agricultural_sciences-agricultural_biotechnology",
        "scientific_subdomain-agricultural_sciences-agriculture_forestry_and_fisheries",
        "scientific_subdomain-agricultural_sciences-animal_and_dairy_sciences",
        "scientific_subdomain-agricultural_sciences-other_agricultural_sciences",
        "scientific_subdomain-agricultural_sciences-veterinary_sciences",
    ],
    "scientific_domain-engineering_and_technology": [
        "scientific_subdomain-engineering_and_technology-chemical_engineering",
        "scientific_subdomain-engineering_and_technology-civil_engineering",
        "scientific_subdomain-engineering_and_technology-electrical_electronic_and_information_engineering",
        "scientific_subdomain-engineering_and_technology-environmental_biotechnology",
        "scientific_subdomain-engineering_and_technology-environmental_engineering",
        "scientific_subdomain-engineering_and_technology-industrial_biotechnology",
        "scientific_subdomain-engineering_and_technology-mechanical_engineering",
        "scientific_subdomain-engineering_and_technology-medical_engineering",
        "scientific_subdomain-engineering_and_technology-nanotechnology",
        "scientific_subdomain-engineering_and_technology-other_engineering_and_technology_sciences",
    ],
    "scientific_domain-generic": ["scientific_subdomain-generic-generic"],
    "scientific_domain-humanities": [
        "scientific_subdomain-humanities-arts",
        "scientific_subdomain-humanities-history_and_archaeology",
        "scientific_subdomain-humanities-languages_and_literature",
        "scientific_subdomain-humanities-other_humanities",
        "scientific_subdomain-humanities-philosophy_ethics_and_religion",
    ],
    "scientific_domain-medical_and_health_sciences": [
        "scientific_subdomain-medical_and_health_sciences-basic_medicine",
        "scientific_subdomain-medical_and_health_sciences-clinical_medicine",
        "scientific_subdomain-medical_and_health_sciences-health_sciences",
        "scientific_subdomain-medical_and_health_sciences-medical_biotechnology",
        "scientific_subdomain-medical_and_health_sciences-other_medical_sciences",
    ],
    "scientific_domain-natural_sciences": [
        "scientific_subdomain-natural_sciences-biological_sciences",
        "scientific_subdomain-natural_sciences-chemical_sciences",
        "scientific_subdomain-natural_sciences-computer_and_information_sciences",
        "scientific_subdomain-natural_sciences-earth_and_related_environmental_sciences",
        "scientific_subdomain-natural_sciences-mathematics",
        "scientific_subdomain-natural_sciences-other_natural_sciences",
        "scientific_subdomain-natural_sciences-physical_sciences",
    ],
    "scientific_domain-other": ["scientific_subdomain-other-other"],
    "scientific_domain-social_sciences": [
        "scientific_subdomain-social_sciences-economics_and_business",
        "scientific_subdomain-social_sciences-educational_sciences",
        "scientific_subdomain-social_sciences-law",
        "scientific_subdomain-social_sciences-media_and_communications",
        "scientific_subdomain-social_sciences-other_social_sciences",
        "scientific_subdomain-social_sciences-political_sciences",
        "scientific_subdomain-social_sciences-psychology",
        "scientific_subdomain-social_sciences-social_and_economic_geography",
        "scientific_subdomain-social_sciences-sociology",
    ],
}

categories_and_subcategories_dict = {
    "category-aggregators_and_integrators-aggregators_and_integrators": [
        "subcategory-aggregators_and_integrators-aggregators_and_integrators-applications",
        "subcategory-aggregators_and_integrators-aggregators_and_integrators-data",
        "subcategory-aggregators_and_integrators-aggregators_and_integrators-other",
        "subcategory-aggregators_and_integrators-aggregators_and_integrators-services",
        "subcategory-aggregators_and_integrators-aggregators_and_integrators-software",
    ],
    "category-applications-applications": [
        "subcategory-applications-applications-application_repository",
        "subcategory-applications-applications-business",
        "subcategory-applications-applications-collaboration",
        "subcategory-applications-applications-communication",
        "subcategory-applications-applications-education",
        "subcategory-applications-applications-other",
        "subcategory-applications-applications-productivity",
        "subcategory-applications-applications-social_networking",
        "subcategory-applications-applications-utilities",
    ],
    "category-compute-compute": [
        "subcategory-compute-compute-container_management",
        "subcategory-compute-compute-job_execution",
        "subcategory-compute-compute-orchestration",
        "subcategory-compute-compute-other",
        "subcategory-compute-compute-serverless_applications_repository",
        "subcategory-compute-compute-virtual_machine_management",
        "subcategory-compute-compute-workload_management",
    ],
    "category-consultancy_and_support-consultancy_and_support": [
        "subcategory-consultancy_and_support-consultancy_and_support-application_optimisation",
        "subcategory-consultancy_and_support-consultancy_and_support-application_porting",
        "subcategory-consultancy_and_support-consultancy_and_support-application_scaling",
        "subcategory-consultancy_and_support-consultancy_and_support-audit_and_assessment",
        "subcategory-consultancy_and_support-consultancy_and_support-benchmarking",
        "subcategory-consultancy_and_support-consultancy_and_support-calibration",
        "subcategory-consultancy_and_support-consultancy_and_support-certification",
        "subcategory-consultancy_and_support-consultancy_and_support-consulting",
        "subcategory-consultancy_and_support-consultancy_and_support-methodology_development",
        "subcategory-consultancy_and_support-consultancy_and_support-methodology_and_simulation",
        "subcategory-consultancy_and_support-consultancy_and_support-other",
        "subcategory-consultancy_and_support-consultancy_and_support-prototype_development",
        "subcategory-consultancy_and_support-consultancy_and_support-software_development",
        "subcategory-consultancy_and_support-consultancy_and_support-technology_transfer",
        "subcategory-consultancy_and_support-consultancy_and_support-testing",
    ],
    "category-data-data": [
        "subcategory-data-data-clinical_trial_data",
        "subcategory-data-data-data_archives",
        "subcategory-data-data-epidemiological_data",
        "subcategory-data-data-government_and_agency_data",
        "subcategory-data-data-online_service_data",
        "subcategory-data-data-other",
        "subcategory-data-data-scientific_research_data",
        "subcategory-data-data-statistical_data",
    ],
    "category-data_analysis-data_analysis": [
        "subcategory-data_analysis-data_analysis-2d_3d_digitisation",
        "subcategory-data_analysis-data_analysis-artificial_intelligence",
        "subcategory-data_analysis-data_analysis-data_exploration",
        "subcategory-data_analysis-data_analysis-forecast",
        "subcategory-data_analysis-data_analysis-image_data_analysis",
        "subcategory-data_analysis-data_analysis-machine_learning",
        "subcategory-data_analysis-data_analysis-other",
        "subcategory-data_analysis-data_analysis-visualization",
        "subcategory-data_analysis-data_analysis-workflows",
    ],
    "category-data_management-data_management": [
        "subcategory-data_management-data_management-access",
        "subcategory-data_management-data_management-annotation",
        "subcategory-data_management-data_management-anonymisation",
        "subcategory-data_management-data_management-brokering",
        "subcategory-data_management-data_management-digitisation",
        "subcategory-data_management-data_management-discovery",
        "subcategory-data_management-data_management-embargo",
        "subcategory-data_management-data_management-interlinking",
        "subcategory-data_management-data_management-maintenance",
        "subcategory-data_management-data_management-mining",
        "subcategory-data_management-data_management-other",
        "subcategory-data_management-data_management-persistent_identifier",
        "subcategory-data_management-data_management-preservation",
        "subcategory-data_management-data_management-processing_and_analysis-data_management-publishing",
        "subcategory-data_management-data_management-registration",
        "subcategory-data_management-data_management-transfer",
        "subcategory-data_management-data_management-validation",
    ],
    "category-data_storage-data_storage": [
        "subcategory-data_storage-data_storage-archive",
        "subcategory-data_storage-data_storage-backup",
        "subcategory-data_storage-data_storage-data",
        "subcategory-data_storage-data_storage-digital_preservation",
        "subcategory-data_storage-data_storage-disk",
        "subcategory-data_storage-data_storage-file",
        "subcategory-data_storage-data_storage-online",
        "subcategory-data_storage-data_storage-other",
        "subcategory-data_storage-data_storage-queue",
        "subcategory-data_storage-data_storage-recovery",
        "subcategory-data_storage-data_storage-replicated",
        "subcategory-data_storage-data_storage-synchronised",
    ],
    "category-development_resources-development_resources": [
        "subcategory-development_resources-development_resources-apis_repository_gateway",
        "subcategory-development_resources-development_resources-developer_tools",
        "subcategory-development_resources-development_resources-other",
        "subcategory-development_resources-development_resources-software_development_kits",
        "subcategory-development_resources-development_resources-software_libraries",
    ],
    "category-education_and_training-education_and_training": [
        "subcategory-education_and_training-education_and_training-in_house_courses",
        "subcategory-education_and_training-education_and_training-online_courses",
        "subcategory-education_and_training-education_and_training-open_registration_courses",
        "subcategory-education_and_training-education_and_training-other",
        "subcategory-education_and_training-education_and_training-related_training",
        "subcategory-education_and_training-education_and_training-required_training",
        "subcategory-education_and_training-education_and_training-training_platform",
        "subcategory-education_and_training-education_and_training-training_tool",
    ],
    "category-instrument_and_equipment-instrument_and_equipment": [
        "subcategory-instrument_and_equipment-instrument_and_equipment-chromatographer",
        "subcategory-instrument_and_equipment-instrument_and_equipment-cytometer",
        "subcategory-instrument_and_equipment-instrument_and_equipment-digitisation_equipment",
        "subcategory-instrument_and_equipment-instrument_and_equipment-geophysical",
        "subcategory-instrument_and_equipment-instrument_and_equipment-laser",
        "subcategory-instrument_and_equipment-instrument_and_equipment-microscopy",
        "subcategory-instrument_and_equipment-instrument_and_equipment-monument_maintenance_equipment",
        "subcategory-instrument_and_equipment-instrument_and_equipment-other",
        "subcategory-instrument_and_equipment-instrument_and_equipment-radiation",
        "subcategory-instrument_and_equipment-instrument_and_equipment-spectrometer",
        "subcategory-instrument_and_equipment-instrument_and_equipment-spectrophotometer",
    ],
    "category-material_storage-material_storage": [
        "subcategory-material_storage-material_storage-archiving",
        "subcategory-material_storage-material_storage-assembly",
        "subcategory-material_storage-material_storage-disposal",
        "subcategory-material_storage-material_storage-fulfillment",
        "subcategory-material_storage-material_storage-other",
        "subcategory-material_storage-material_storage-packaging",
        "subcategory-material_storage-material_storage-preservation",
        "subcategory-material_storage-material_storage-quality_inspecting",
        "subcategory-material_storage-material_storage-repository",
        "subcategory-material_storage-material_storage-reworking",
        "subcategory-material_storage-material_storage-sorting",
        "subcategory-material_storage-material_storage-warehousing",
    ],
    "category-measurement_and_materials_analysis-measurement_and_materials_analysis": [
        "subcategory-measurement_and_materials_analysis-measurement_and_materials_analysis-analysis",
        "subcategory-measurement_and_materials_analysis-measurement_and_materials_analysis-characterisation",
        "subcategory-measurement_and_materials_analysis-measurement_and_materials_analysis-maintenance_and_modification",
        "subcategory-measurement_and_materials_analysis-measurement_and_materials_analysis-other",
        "subcategory-measurement_and_materials_analysis-measurement_and_materials_analysis-production",
        "subcategory-measurement_and_materials_analysis-measurement_and_materials_analysis-testing_and_validation",
        "subcategory-measurement_and_materials_analysis-measurement_and_materials_analysis-validation",
        "subcategory-measurement_and_materials_analysis-measurement_and_materials_analysis-workflows",
    ],
    "category-network-network": [
        "subcategory-network-network-content_delivery_network",
        "subcategory-network-network-direct_connect",
        "subcategory-network-network-exchange",
        "subcategory-network-network-load_balancer",
        "subcategory-network-network-other",
        "subcategory-network-network-traffic_manager",
        "subcategory-network-network-virtual_network",
        "subcategory-network-network-vpn_gateway",
    ],
    "category-operations_and_infrastructure_management-operations_and_infrastructure_management": [
        "subcategory-operations_and_infrastructure_management-operations_and_infrastructure_management-accounting",
        "subcategory-operations_and_infrastructure_management-operations_and_infrastructure_management-analysis",
        "subcategory-operations_and_infrastructure_management-operations_and_infrastructure_management-billing",
        "subcategory-operations_and_infrastructure_management-operations_and_infrastructure_management-configuration",
        "subcategory-operations_and_infrastructure_management-operations_and_infrastructure_management-coordination",
        "subcategory-operations_and_infrastructure_management-operations_and_infrastructure_management-helpdesk",
        "subcategory-operations_and_infrastructure_management-operations_and_infrastructure_management-monitoring",
        "subcategory-operations_and_infrastructure_management-operations_and_infrastructure_management-order_management",
        "subcategory-operations_and_infrastructure_management-operations_and_infrastructure_management-other",
        "subcategory-operations_and_infrastructure_management-operations_and_infrastructure_management-transportation",
        "subcategory-operations_and_infrastructure_management-operations_and_infrastructure_management-utilities",
    ],
    "category-other-other": ["subcategory-other-other"],
    "category-samples-samples": [
        "subcategory-samples-samples-biological_samples",
        "subcategory-samples-samples-characterisation",
        "subcategory-samples-samples-chemical_compounds_library",
        "subcategory-samples-samples-other",
        "subcategory-samples-samples-preparation",
    ],
    "category-scholarly_communication-scholarly_communication": [
        "subcategory-scholarly_communication-scholarly_communication-analysis",
        "subcategory-scholarly_communication-scholarly_communication-assessment",
        "subcategory-scholarly_communication-scholarly_communication-discovery",
        "subcategory-scholarly_communication-scholarly_communication-other",
        "subcategory-scholarly_communication-scholarly_communication-outreach",
        "subcategory-scholarly_communication-scholarly_communication-preparation",
        "subcategory-scholarly_communication-scholarly_communication-publication",
        "subcategory-scholarly_communication-scholarly_communication-writing",
    ],
    "category-security_and_identity-security_and_identity": [
        "subcategory-security_and_identity-security_and_identity-certification_authority",
        "subcategory-security_and_identity-security_and_identity-coordination",
        "subcategory-security_and_identity-security_and_identity-firewall",
        "subcategory-security_and_identity-security_and_identity-group_management",
        "subcategory-security_and_identity-security_and_identity-identity_and_access_management",
        "subcategory-security_and_identity-security_and_identity-other",
        "subcategory-security_and_identity-security_and_identity-single_sign_on",
        "subcategory-security_and_identity-security_and_identity-threat_protection",
        "subcategory-security_and_identity-security_and_identity-tools",
        "subcategory-security_and_identity-security_and_identity-user_authentication",
    ],
    "category-software-software": [
        "subcategory-software-software-libraries",
        "subcategory-software-software-other",
        "subcategory-software-software-platform",
        "subcategory-software-software-software_package",
        "subcategory-software-software-software_repository",
    ],
}

target_users_list = [
    "target_user-businesses",
    "target_user-funders",
    "target_user-innovators",
    "target_user-other",
    "target_user-policy_makers",
    "target_user-providers",
    "target_user-research_communities",
    "target_user-research_groups",
    "target_user-research_infrastructure_managers",
    "target_user-research_managers",
    "target_user-research_networks",
    "target_user-research_organisations",
    "target_user-research_projects",
    "target_user-researchers",
    "target_user-resource_managers",
    "target_user-resource_provider_managers",
    "target_user-students",
]

access_types_list = [
    "access_type-mail_in",
    "access_type-other",
    "access_type-physical",
    "access_type-remote",
    "access_type-virtual",
]

access_modes_list = [
    "access_mode-free",
    "access_mode-free_conditionally",
    "access_mode-other",
    "access_mode-paid",
    "access_mode-peer_reviewed",
]
