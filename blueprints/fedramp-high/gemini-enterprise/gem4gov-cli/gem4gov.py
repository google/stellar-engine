import sys
import click
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.api_core.client_options import ClientOptions
import subprocess
import random
import string
import json
import yaml
import os
import time
from data_stores import (
    generate_id,
    validate_data_store,
    create_gcs_data_store,
    import_gcs_documents,
    get_bq_schema,
    transform_bq_schema,
    create_bq_data_store,
    create_data_store_schema,
    import_bq_documents,
    list_data_stores,
)
from auth import (
    get_credentials,
    force_reauthentication,
    check_roles,
)

# Global Varibles used in prompts
supported_aw_boundaries = "FedRAMP High, IL4, IL5"
required_apis = "Vertex AI, Discovery Engine, Cloud Resource Manager, Cloud Key Management Service (KMS), Identity and Access Management (IAM), Service Usage, Cloud Storage, BigQuery"
supported_data_stores = "Cloud Storage, BigQuery"

@click.group()
def cli():
    """A command-line tool to onboard government customers to Gemini for Government."""
    pass

##############################################################
################         gem4gov init         ################
##############################################################

@cli.command()
def init():
    """Initializes the Gemini for Government CLI and authenticates the user."""
    click.echo("Initializing Gemini for Government CLI...")
    # Unset any existing project and billing/quota_project configurations
    try:
        subprocess.run(['gcloud', 'config', 'unset', 'project'], check=True, capture_output=True)
        subprocess.run(['gcloud', 'config', 'unset', 'billing/quota_project'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Ignore errors if the properties are not set
        pass
    force_reauthentication()
    project_id = click.prompt('Please enter the GCP Project ID', type=str).strip()
    try:
        subprocess.run(['gcloud', 'config', 'set', 'project', project_id], check=True, capture_output=True)
        subprocess.run(['gcloud', 'config', 'set', 'billing/quota_project', project_id], check=True, capture_output=True)
        subprocess.run(['gcloud', 'auth', 'application-default', 'set-quota-project', project_id], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        click.echo("Could not set the gcloud project configuration. Please ensure gcloud is installed and configured correctly.")
        click.echo(click.style("Exiting Onboarding process...", fg="red"))
        sys.exit(1)
    credentials = get_credentials()
    click.echo(f"Successfully set project ID to: {project_id}")

##############################################################
################       gem4gov onboard        ################
##############################################################

@cli.command()
def onboard():
    """Onboards a new government customer."""
    click.echo("Starting the onboarding process...")
    credentials = get_credentials()
    click.echo(click.style("Welcome to the Gemini for Government Onboarding Tool!", fg='green'))
    click.echo(nl=True)
    click.echo(click.style(f"We will start off with the most important topic, compliance. Google's Assured Workloads simplifies management and configuration of regulated workloads by applying predefined control packages to folders. Gemini for Government currently supports the following regulatory data boundaries: {supported_aw_boundaries}", fg='yellow'))
    click.echo("What compliance regime will Gemini for Government be deployed in?")
    click.echo("1) FedRAMP High")
    click.echo("2) IL4")
    click.echo("3) IL5")
    click.echo("4) None")
    compliance_regime_id = click.prompt('Please enter the number for your response', type=click.Choice(['1', '2', '3', '4']), default = '1', show_default = False)
    
    click.echo(nl=True)
    click.echo(nl=True)

    click.echo(click.style("The Gemini for Government solution is essentially comprised of Gemini Enterprise deployed within a protected / regulated environment via Assured Workloads. The GCP Project that Gemini for Government will be deployed in must already be created and reside within an Assured Workload folder.", fg='yellow'))
    if click.confirm('Have you already created a GCP Project within an Assured Workloads folder (if necessary)?'):
        project_id = click.prompt('Please enter the GCP Project ID', type=str).strip()
    else:
        click.echo(click.style("Please create an Assured Workloads folder and a GCP Project within that folder before continuing.", fg='red'))
        click.echo(click.style("Exiting Onboarding process...", fg="red"))
        sys.exit(1)

    try:
        subprocess.run(['gcloud', 'config', 'set', 'project', project_id], check=True, capture_output=True)
        subprocess.run(['gcloud', 'config', 'set', 'billing/quota_project', project_id], check=True, capture_output=True)
        subprocess.run(['gcloud', 'auth', 'application-default', 'set-quota-project', project_id], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        click.echo("Could not set the gcloud project configuration. Please ensure gcloud is installed and configured correctly.")
        click.echo(click.style("Exiting Onboarding process...", fg="red"))
        sys.exit(1)
    
    # Set the quota project on the credentials
    credentials = credentials.with_quota_project(project_id)

    click.echo(nl=True)
    click.echo(nl=True)
    
    click.echo(click.style("Now, let's make sure you have all of the IAM roles needed on this project to successfully run through the Onboarding process.", fg='yellow'))
    if not check_roles(credentials, project_id):
        click.echo(click.style("Please grant your user these IAM roles OR confirm that your current set of roles gives you the same permissions that make up these missing roles (i.e. Owner).", fg="red"))
        if not click.confirm('Would you like to continue the Onboarding process anyway?'):
            click.echo(click.style("Please grant your user the list of IAM roles found in the README or have another user with those roles run the Onboarding process.", fg='red'))
            click.echo(click.style("Exiting Onboarding process...", fg="red"))
            sys.exit(1)
    
    click.echo(nl=True)
    click.echo(nl=True)

    click.echo(click.style("The Gemini for Government project must have the following APIs enabled:", fg='yellow'))
    click.echo(click.style(f"{required_apis}", fg='yellow'))
    if not check_apis(credentials, project_id):
        return
    
    click.echo(nl=True)
    click.echo(nl=True)

    click.echo(click.style("Checking if the Gemini Enterprise identity provider has been setup already...", fg='yellow'))
    idp_type = check_identity_provider(credentials, project_id)
    workforce_pool_id = None
    workforce_provider_id = None
    if idp_type == "IDP_TYPE_UNSPECIFIED":
        click.echo(click.style("Gemini Enterprise end-users can login using Google Identity or a third-party Identity Provider (via Workforce Identity Federation). The chosen Identity Provider will also be used for ACLs on your data store (if available).", fg='yellow'))
        click.echo("Will end-users log-in to Gemini Enterprise with Google Identity or a third-party Identity Provider (via Workforce Identity Federation)?")
        click.echo("1) Google Identity")
        click.echo("2) Third-Party Identity Provider (Workforce Identity Federation)")
        idp_select = click.prompt('Please enter the number for your response', type=click.Choice(['1', '2']), default = '1', show_default = False)
        if idp_select == '2':
            click.echo(click.style("The Workforce Identity Pool must be configured already and the attribute mapping must be setup for your specific provider.", fg = "yellow"))
            if click.confirm('Have you already configured the Workforce Identity Pool and Provider?'):
                workforce_pool_id = click.prompt('Please enter the Workforce Pool ID (without the "locations/global/workforcePools/" prefix)')
                workforce_provider_id = click.prompt(f'Please enter the Workforce Identity Federation Provider ID (without the "locations/global/workforcePools/{workforce_pool_id}/providers/" prefix)')
            else:
                click.echo(click.style("Please configure a Workforce Identity Pool and Provider before continuing the Onboarding process", fg='red'))
                click.echo(click.style("Exiting Onboarding process...", fg="red"))
                sys.exit(1)
        idp_type = configure_identity_provider(credentials, project_id, idp_select, workforce_pool_id)
    click.echo(nl=True)
    click.echo(nl=True)

    click.echo(click.style("Checking if the Gemini Enterprise CMEK configuration has been setup already...", fg='yellow'))
    cmek_state = check_cmek(credentials, project_id)
    if cmek_state == "STATE_UNSPECIFIED":
        click.echo('You do not have a CMEK key set for the Gemini Enterprise "us" multi-region.')
        project_number = get_project_number(credentials, project_id)
        click.echo(click.style("You can use customer-managed encryption keys (CMEKs) in Cloud KMS to encrypt your Gemini Enterprise data stores. Cloud KMS keys gives you control over the key's protection level, location, rotation schedule, usage and access permissions, and cryptographic boundaries.", fg='yellow'))
        click.echo('Do you have an existing Cloud KMS key in the "us" multi-region that you would like to register with Gemini Enterprise or would you like to create a new one?')
        click.echo('1) Existing Cloud KMS CMEK in the "us" multi-region')
        click.echo('2) Create a new Cloud KMS CMEK in the "us" multi-region')
        click.echo('3) Continue without Gemini Enterprise CMEK encryption')
        cmek_action = click.prompt('Please enter the number for your response', type=click.Choice(['1', '2', '3']), default = '3', show_default = False)

        if cmek_action == '1':
            while True:
                kms_key_name = click.prompt('Please enter the Cloud KMS key name (projects/KMS_PROJECT_ID/locations/us/keyRings/KEY_RING/cryptoKeys/KEY_NAME)', type=str).strip()
                if validate_kms_key(credentials, kms_key_name):
                    if grant_kms_permissions(credentials, kms_key_name, project_number):
                        configure_cmek(credentials, project_id, kms_key_name)
                        break
                    else:
                        click.echo("Failed to grant KMS permissions. Please check the error and try again.")
                        if not click.confirm('Would you like to try again?'):
                            click.echo(click.style("Exiting Onboarding process...", fg="red"))
                            sys.exit(1)
                else:
                    if not click.confirm('The KMS key is invalid. Would you like to try again?'):
                        click.echo(click.style("Exiting Onboarding process...", fg="red"))
                        sys.exit(1)

        elif cmek_action == '2':
            click.echo('Please navigate to https://console.cloud.google.com/security/kms/keyrings and create a Cloud KMS Key Ring in the "us" multi-region.')
            click.echo('Then create a Crypto Key within that Key Ring with the following attributes:')
            click.echo('- Protection level: HSM')
            click.echo('- Key material: HSM-generated key (key is generated for you) OR Imported key (import your own key material)')
            click.echo('- Purpose: Symmetric encrypt/decrypt')
            click.echo('- Key rotation: 90 days')
            click.echo('You may leave all other settings as their default values.')
            while True:
                kms_key_name = click.prompt('Please enter the Cloud KMS key name (projects/KMS_PROJECT_ID/locations/us/keyRings/KEY_RING/cryptoKeys/KEY_NAME)', type=str).strip()
                if validate_kms_key(credentials, kms_key_name):
                    if grant_kms_permissions(credentials, kms_key_name, project_number):
                        configure_cmek(credentials, project_id, kms_key_name)
                        break
                    else:
                        click.echo("Failed to grant KMS permissions. Please check the error and try again.")
                        if not click.confirm('Would you like to try again?'):
                            click.echo(click.style("Exiting Onboarding process...", fg="red"))
                            sys.exit(1)
                else:
                    if not click.confirm('The KMS key is invalid. Would you like to try again?'):
                        click.echo(click.style("Exiting Onboarding process...", fg="red"))
                        sys.exit(1)
        else:
            click.echo('You can always setup the Gemini Enterprise CMEK configuration at a later time.')
            click.echo('NOTE: Ensure that Gemini Enterprise CMEK configuration is setup before adding any data stores to your Gemini Enterprise application.')

    click.echo(nl=True)
    click.echo(nl=True)

    click.echo(click.style("There are 3 Gemini Enterprise application types that are completely dependent on the number of data stores connect to the application.", fg='yellow'))
    click.echo(nl=True)
    click.echo(click.style("DEFAULT: The Default application type allows end-users to interact with the Gemini assistant, utilize the \"Made-by-Google\" Deep Research agent, and ground on Enterprise Web Search or uploaded documents.", fg='yellow'))
    click.echo(click.style("SEARCH ENGINE: The Search Engine application type provides the default experience + 1 Cloud Storage / BigQuery data store that end-users can interact with in a conversational, generative AI-powered search experience)", fg='yellow'))
    click.echo(click.style("BLENDED SEARCH: Blended Search application type provides the default experience + 2 or more Cloud Storage / BigQuery data stores that end-users can interact with in a conversational, generative AI-powered search experience)", fg='yellow'))
    click.echo(nl=True)
    click.echo(click.style("IMPORTANT! You are NOT ABLE TO ADD DATA STORES after an application is created (unless it is a Blended Search application and the total number of data stores >= 2)", fg='red'))
    click.echo(click.style("IMPORTANT! In the future, to add data stores, you will need to delete the existing application and re-run the onboarding process to create the desired application type", fg='red'))
    
    click.echo("Please select the Gemini Enterprise application type that you would like to create:")
    click.echo("1) Default")
    click.echo("2) Search Engine (1 data store)")
    click.echo("3) Blended Search (>=2 data stores)")
    app_type = click.prompt('Please enter the number for your response', type=click.Choice(['1', '2', '3']), default = '1', show_default = False)
    
    data_store_list = []
    valid_data_stores = []
    invalid_data_stores = []

    # Validate / Create data stores for Search Engine / Blended Search applications
    if app_type in ['2', '3']:
        if cmek_action == '3':
            click.echo('It is highly reccommended to setup Gemini Enterprise CMEK configuration before creating any data stores and associating them with your Gemini Enterprise application.')
            click.echo('Please review the CMEK configuration limitations before proceeding: https://docs.cloud.google.com/gemini/enterprise/docs/cmek#limitations')
            if not click.confirm('Would you like to continue without setting up Gemini Enterprise CMEK configuration?'):
                click.echo(click.style('Please run `gem4gov onboard` again to setup Gemini Enterprise CMEK configuration.', fg="red"))
                click.echo(click.style("Exiting Onboarding process...", fg="red"))
                sys.exit(1)
        click.echo(click.style(f"Gemini Enterprise data stores allow end-users to search and ask questions based on a variety of first and third-party datasets. Currently, the only data stores that are available in Gemini for Governement customers are: {supported_data_stores}", fg='yellow'))
        while True:
            if click.confirm('Do you have an existing data store(s) already created and loaded with data?'):
                # User specified they have existing data stores
                data_store_input = click.prompt('Please enter a comma-separated list of data stores that you would like to connect to Gemini Enterprise', type=str).strip()
                data_store_list = [item.strip() for item in data_store_input.split(',')]
                    
            # User specified they do not have existing data stores
            else:
                while True:
                    # User indicated they would like to create a new data store
                    click.echo('What type of data store would you like to setup?')
                    click.echo("1) Google Cloud Storage")
                    click.echo("2) BigQuery")
                    data_store_type = click.prompt('Please enter the number for your response', type=click.Choice(['1', '2']), default='1', show_default=False)
                    display_name = click.prompt('Please enter a Display Name for the data store (end-users will see this in the Gemini Enterprise UI)')
                    
                    # Create Cloud Storage data store
                    if data_store_type == '1':
                        if not click.confirm('Does the Cloud Storage bucket for this data store exist and contain data?'):
                            click.echo(click.style("Please create and populate the Cloud Storage bucket before setting up the data store.", fg='red'))
                        else:
                            data_store_id = generate_id('g4g-gem-ent-ds-gcs-')
                            gcs_bucket = click.prompt('Please enter the name of the Google Cloud Storage bucket where the documents are stored (without the "gs://" prefix)').strip()
                            click.echo(click.style("The path prefix should be the path to the documents within the GCS bucket. Do not include a leading or trailing slash. For example, if your documents are in 'gs://my-bucket/docs/2024', the prefix would be 'docs/2024'.", fg='yellow'))
                            path_prefix = click.prompt('Please enter the path prefix to the documents (if necessary)', default='').strip()
                            # Clean up the prefix to avoid issues with leading/trailing slashes
                            path_prefix = path_prefix.strip('/')

                            if path_prefix:
                                # Append wildcard to non-empty prefix
                                path_prefix = f"{path_prefix}/**"
                            else:
                                # If no prefix is provided, import all documents from the bucket root
                                path_prefix = "**"
                            click.echo(f"Using path prefix: {path_prefix}")
                            create_gcs_data_store(credentials, project_id, data_store_id, display_name)
                            import_gcs_documents(credentials, project_id, data_store_id, gcs_bucket, path_prefix)
                            click.echo(f"Google Cloud Storage data store created and indexing operation started successfully...")
                            data_store_list.append(data_store_id)

                    # Create BigQuery data store
                    elif data_store_type == '2':
                        if not click.confirm('Does the BigQuery dataset / table for this data store exist and contain data?'):
                            click.echo(click.style("Please create and populate the dataset / table before setting up the data store.", fg='red'))
                        else:
                            data_store_id = generate_id('g4g-gem-ent-ds-bq-')
                            id_property = {'id': ''}
                            key_properties = {'title': '', 'description': '', 'uri': '', 'category': ''}
                            dataset = click.prompt('Please enter the BigQuery dataset where the data is stored')
                            table = click.prompt('Please enter the BigQuery table where the data is stored')
                            bq_schema = get_bq_schema(credentials, project_id, dataset, table)
                            if bq_schema:
                                fields = [field['name'] for field in bq_schema.get('fields', [])]
                                if len(fields) > 0:
                                    click.echo(nl=True)
                                    click.echo(nl=True)
                                    click.echo(click.style('Each document (record) in the BigQuery table must have a unique ID. Select the schema field that should be used as the unique ID. If one does not exist, select "Auto".', fg="yellow"))
                                    for i, field in enumerate(fields):
                                        click.echo(f"{i + 1}) {field}")
                                    auto_option = len(fields) + 1
                                    click.echo(f"{auto_option}) Auto")
                                    field_choice = click.prompt(
                                        'Please enter the number for your response', 
                                        type=click.IntRange(1, len(fields) + 1)
                                    )
                                    if field_choice != auto_option:
                                        id_field_name = fields[field_choice - 1]
                                        id_property['id'] = id_field_name
                                        click.echo(f'Using schema field "{id_field_name}" as the unique document ID.')
                                    else:
                                        id_property['id'] = 'auto'
                                        click.echo(f'Autogenerating unique document ID.')
                                    
                                    click.echo(nl=True)
                                    click.echo(nl=True)

                                    click.echo(click.style('To help clarify the semantic meaning of documents (records) in the BigQuery structured dataset, the following set of predefined keywords can be assigned to fields in the schema:', fg="yellow"))
                                    click.echo(click.style('"title", "description", "uri", "category"', fg='yellow'))
                                    click.echo(click.style('NOTE: The predefined keyword and the selected schema field name do not need to match.', fg='yellow'))

                                    for key in key_properties:
                                        click.echo('----------------------------------------------------------')
                                        click.echo(click.style(f'Please select the schema field to be used as the predefined keyword "{key}":', fg='yellow'))
                                        click.echo(click.style('NOTE: If the predefined keyword is not applicable, select the number for "N/A"', fg='yellow'))

                                        for i, field in enumerate(fields):
                                            click.echo(f"{i + 1}) {field}")
                                        na_option = len(fields) + 1
                                        click.echo(f"{na_option}) N/A")
                                    
                                        field_choice = click.prompt(
                                            'Please enter the number for your response', 
                                            type=click.IntRange(1, len(fields) + 1)
                                        )

                                        if field_choice != na_option:
                                            id_field_name = fields[field_choice - 1]
                                            key_properties[key] = id_field_name
                                            click.echo(f'Using schema field "{id_field_name}" as the "{key}" predefined keyword.')
                                        else:
                                            click.echo(f'"{key}" predefined keyword is not applicable to this schema.')
                                        
                                    discovery_engine_schema = transform_bq_schema(bq_schema, key_properties)
                                    create_bq_data_store(credentials, project_id, data_store_id, display_name, dataset, table)
                                    create_data_store_schema(credentials, project_id, data_store_id, discovery_engine_schema)
                                    import_bq_documents(credentials, project_id, data_store_id, dataset, table, id_property)
                                    click.echo(f"BigQuery data store created and indexing operation started successfully...")
                                    data_store_list.append(data_store_id)

                                else:
                                    click.echo(click.style(f'Could not find any fields in the "{table}" table within the "{dataset}" BigQuery dataset. Please ensure the BigQuery dataset / table entered exists and is populated with data.'), fg='red')
                            else:
                                click.echo(click.style(f'Could not find a schema for the "{table}" table within the "{dataset}" BigQuery dataset. Please ensure the BigQuery dataset / table entered exists and is populated with data.'), fg='red')

                    if not click.confirm('Would you like to create another data store?'):
                        break

            # User did not enter any data stores
            if len(data_store_list) == 0:
                if not click.confirm('Would you like to continue the Onboarding process for a Default Gemini Enterpise application?'):
                    click.echo(click.style("Exiting Onboarding process...", fg="red"))
                    sys.exit(1)
                else:
                    app_type = '1'
                    break

            # Validate the data stores
            for ds_id in data_store_list:
                validated_ds = validate_data_store(credentials, project_id, ds_id)
                if validated_ds.get('valid') == False:
                    invalid_data_stores.append(validated_ds)
                else:
                    valid_data_stores.append(validated_ds)
            
            # User entered at least 1 invalid data store
            if len(invalid_data_stores) > 0:
                # List invalid data stores and then prompt user to enter the list of data stores again
                click.echo(click.style("The following data stores are invalid and cannot be connected to the Gemini Enterprise application:", fg="red"))
                for ds in invalid_data_stores:
                    if ds.get('display_name', None) == None:
                        click.echo(click.style(f"- {ds["id"]} (Does not exist)", fg="red"))
                    elif ds.get('kms_key_name', None) == None:
                        click.echo(click.style(f"- {ds["id"]} (Not CMEK encrypted)", fg="red"))
                    else:
                        click.echo(click.style(f"- {ds["id"]} (Incompatible)", fg="red"))
                data_store_list = []
                valid_data_stores = []
                invalid_data_stores = []

            # User entered all valid data stores
            else:
                # List valid data stores and prompt the user to confirm the list
                click.echo(click.style("The following data stores have been validated and will be connected to the Gemini Enterprise application:", fg="yellow"))
                for ds in valid_data_stores:
                    click.echo(click.style(f"- {ds["id"]} ({ds["display_name"]})", fg="yellow"))

                if click.confirm('Please confirm that you would like to connect the above list of data stores to the Gemini Enterprise application'):
                    break
                else:
                    data_store_list = []
                    valid_data_stores = []
                    invalid_data_stores = []            
    
    click.echo(nl=True)
    click.echo(nl=True)

    if app_type == '1':
        click.echo(click.style("Let's now create the Gemini Enterprise application and configure some of it's default settings to comply with the regulatory boundary indicated (if applicable)", fg='yellow'))
    else:
        click.echo(click.style("Let's now create the Gemini Enterprise application, connect the data store(s), and configure some of it's default settings to comply with the regulatory boundary indicated (if applicable)", fg='yellow'))
    engine_display_name = click.prompt('Please enter a Display Name for the Gemini Enterprise application').strip()
    company_name = click.prompt('Please enter the Agency / Department Name (no abbreviations)').strip()
    click.echo(nl=True)
    engine_id = generate_id('g4g-gem-ent-app-')
    create_engine(credentials, project_id, engine_id, engine_display_name, company_name, data_store_list)
    if idp_type == "THIRD_PARTY" and (workforce_pool_id and workforce_provider_id):
        configure_idp_for_widget(credentials, project_id, engine_id, workforce_pool_id, workforce_provider_id)
    if idp_type == "THIRD_PARTY" and ((workforce_pool_id is None) or (workforce_provider_id is None)):
        click.echo(nl=True)
        click.echo(nl=True)
        click.echo(click.style("Let's now configure Workforce Identity Federation for the Gemini Enterprise application", fg='yellow'))
        workforce_pool_id = click.prompt('Please enter the Workforce Pool ID (without the "locations/global/workforcePools/" prefix)')
        workforce_provider_id = click.prompt(f'Please enter the Workforce Identity Federation Provider ID (without the "locations/global/workforcePools/{workforce_pool_id}/providers/" prefix)')
        configure_idp_for_widget(credentials, project_id, engine_id, workforce_pool_id, workforce_provider_id)

    click.echo(nl=True)
    click.echo(nl=True)

    if compliance_regime_id == '1':
        click.echo(click.style("Gemini Enterprise contains default features that are not yet authorized for FedRAMP High and must be disabled. These features are currently:", fg="yellow"))
        click.echo(click.style("- Grounding with OneDrive / Google Drive File Uploads", fg="yellow"))
        click.echo(click.style("- Grounding with Google Search", fg="yellow"))
        click.echo(click.style("- Image / Video Generation", fg="yellow"))
        click.echo(click.style("- Implicit Model Data Caching", fg="yellow"))
        click.echo(click.style("- Knowledge Graph / People Connectors", fg="yellow"))
        click.echo(click.style("- Location Context", fg="yellow"))
        click.echo(click.style("- Memory and Customization", fg="yellow"))
        click.echo(click.style("- Model Armor", fg="yellow"))
        click.echo(click.style("- NotebookLM Enterprise", fg="yellow"))
        click.echo(click.style("- Prompt Gallery", fg="yellow"))
        click.echo(click.style("- Session Sharing", fg="yellow"))
        click.echo(click.style("- User Event Collection", fg="yellow"))
        click.echo(click.style("- User Feedback", fg="yellow"))
        configure_gemini_enterprise_for_fedramp_high(credentials, project_id, engine_id)
    elif compliance_regime_id == '2':
        click.echo(click.style("Gemini Enterprise contains default features that are not yet authorized for IL4 and must be disabled. These features are currently:", fg="yellow"))
        click.echo(click.style("- Grounding with OneDrive / Google Drive File Uploads", fg="yellow"))
        click.echo(click.style("- Grounding with Google Search", fg="yellow"))
        click.echo(click.style("- Image / Video Generation", fg="yellow"))
        click.echo(click.style("- Implicit Model Data Caching", fg="yellow"))
        click.echo(click.style("- Knowledge Graph / People Connectors", fg="yellow"))
        click.echo(click.style("- Location Context", fg="yellow"))
        click.echo(click.style("- Memory and Customization", fg="yellow"))
        click.echo(click.style("- Model Armor", fg="yellow"))
        click.echo(click.style("- NotebookLM Enterprise", fg="yellow"))
        click.echo(click.style("- Prompt Gallery", fg="yellow"))
        click.echo(click.style("- Session Sharing", fg="yellow"))
        click.echo(click.style("- User Event Collection", fg="yellow"))
        click.echo(click.style("- User Feedback", fg="yellow"))
        configure_gemini_enterprise_for_il4(credentials, project_id, engine_id)
    elif compliance_regime_id == '3':
        click.echo(click.style("Gemini Enterprise contains default features that are not yet authorized for IL5 and must be disabled. These features are currently:", fg="yellow"))
        click.echo(click.style("- Grounding with OneDrive / Google Drive File Uploads", fg="yellow"))
        click.echo(click.style("- Grounding with Google Search", fg="yellow"))
        click.echo(click.style("- Image / Video Generation", fg="yellow"))
        click.echo(click.style("- Implicit Model Data Caching", fg="yellow"))
        click.echo(click.style("- Knowledge Graph / People Connectors", fg="yellow"))
        click.echo(click.style("- Location Context", fg="yellow"))
        click.echo(click.style("- Memory and Customization", fg="yellow"))
        click.echo(click.style("- Model Armor", fg="yellow"))
        click.echo(click.style("- NotebookLM Enterprise", fg="yellow"))
        click.echo(click.style("- Prompt Gallery", fg="yellow"))
        click.echo(click.style("- Session Sharing", fg="yellow"))
        click.echo(click.style("- User Event Collection", fg="yellow"))
        click.echo(click.style("- User Feedback", fg="yellow"))
        configure_gemini_enterprise_for_il5(credentials, project_id, engine_id)

    click.echo(nl=True)
    click.echo(nl=True)
    
    config_id = get_widget_config_id(credentials, project_id, engine_id)

    click.echo(click.style("Onboarding process complete!", fg='green'))
    click.echo(click.style(f"Gemini for Government Project ID: {project_id}", fg='green'))
    if data_store_list:
        click.echo(click.style(f"Gemini Enterprise Data Store IDs: {', '.join(data_store_list)}", fg='green'))
    click.echo(click.style(f"Gemini Enterprise Application ID: {engine_id}", fg='green'))
    click.echo(click.style(f"Gemini Enterprise Widget Config ID: {config_id}", fg='green'))

    click.echo(nl=True)
    click.echo(nl=True)
    
    if data_store_list:
        for ds_id in data_store_list:
            click.echo(click.style(f"Data Store URL ({ds_id}): https://console.cloud.google.com/gen-app-builder/locations/us/engines/{engine_id}/collections/default_collection/data-stores/{ds_id}/data/documents?project={project_id}", fg='green'))
    if config_id:
        if workforce_pool_id and workforce_provider_id:
            # URL encode the continue URL
            import urllib.parse
            continue_url = f"https://vertexaisearch.cloud.google/us/home/cid/{config_id}"
            encoded_continue_url = urllib.parse.quote(continue_url, safe='')
            final_url = f"https://auth.cloud.google/signin/locations/global/workforcePools/{workforce_pool_id}/providers/{workforce_provider_id}?continueUrl={encoded_continue_url}&hl=en_US"
            click.echo(click.style(f"Gemini Enterprise UI URL: {final_url}", fg='green'))
        else:
            click.echo(click.style(f"Gemini Enterprise UI URL: https://vertexaisearch.cloud.google.com/us/home/cid/{config_id}?hl=en_US", fg='green'))


##############################################################
################      gem4gov application     ################
##############################################################

@cli.group()
def app():
    """Manage Gemini Enterprise applications."""
    pass

@app.command("create")
@click.option('--project-id', required=True, help='GCP Project ID')
@click.option('--engine-id', default=None, help='Gemini Enterprise Engine ID')
@click.option('--display-name', default=None, help='Display Name for the Gemini Enterprise application')
@click.option('--company-name', default=None, help='Agency / Department Name')
@click.option('--data-stores', default="", help='Comma-separated list of Data Store IDs')
@click.option('--workforce-pool-id', default=None, help='Workforce Identity Pool ID')
@click.option('--workforce-provider-id', default=None, help='Workforce Identity Provider ID')
@click.option('--compliance-regime', type=click.Choice(['FEDRAMP_HIGH', 'IL4', 'IL5', 'NONE']), default=None, help='Compliance Regime')
@click.option('--enable-audit-logs', is_flag=True, default=False, help='Enable Gemini Enterprise Usage Audit logs')
def create_application(project_id, engine_id, display_name, company_name, data_stores, workforce_pool_id, workforce_provider_id, compliance_regime, enable_audit_logs):
    """Creates a Gemini Enterprise application."""
    credentials = get_credentials()
    # split comma separated string into list
    data_store_list = [ds.strip() for ds in data_stores.split(',') if ds.strip()]
    
    # Map compliance regime to internal value
    compliance_regime_id = None
    if compliance_regime == 'FEDRAMP_HIGH':
        compliance_regime_id = '1'
    elif compliance_regime == 'IL4':
        compliance_regime_id = '2'
    elif compliance_regime == 'IL5':
        compliance_regime_id = '3'
    elif compliance_regime == 'NONE':
        compliance_regime_id = '4'

    create_application_logic(credentials, project_id, data_store_list, workforce_pool_id, workforce_provider_id, compliance_regime_id, engine_id, display_name, company_name, enable_audit_logs)


@app.command("update-compliance")
@click.option('--project-id', required=True, help='GCP Project ID')
@click.option('--engine-id', required=True, help='Gemini Enterprise Engine ID')
@click.option('--compliance-regime', required=True, type=click.Choice(['FEDRAMP_HIGH', 'IL4', 'IL5']), help='Compliance Regime')
def update_compliance(project_id, engine_id, compliance_regime):
    """Configures a Gemini Enterprise application for a specific compliance regime."""
    credentials = get_credentials()
    
    if compliance_regime == 'FEDRAMP_HIGH':
        click.echo(click.style("Gemini Enterprise contains default features that are not yet authorized for FedRAMP High and must be disabled. These features are currently:", fg="yellow"))
        click.echo(click.style("- Grounding with OneDrive / Google Drive File Uploads", fg="yellow"))
        click.echo(click.style("- Grounding with Google Search", fg="yellow"))
        click.echo(click.style("- Image / Video Generation", fg="yellow"))
        click.echo(click.style("- Implicit Model Data Caching", fg="yellow"))
        click.echo(click.style("- Knowledge Graph / People Connectors", fg="yellow"))
        click.echo(click.style("- Location Context", fg="yellow"))
        click.echo(click.style("- Memory and Customization", fg="yellow"))
        click.echo(click.style("- Model Armor", fg="yellow"))
        click.echo(click.style("- NotebookLM Enterprise", fg="yellow"))
        click.echo(click.style("- Prompt Gallery", fg="yellow"))
        click.echo(click.style("- Session Sharing", fg="yellow"))
        click.echo(click.style("- User Event Collection", fg="yellow"))
        click.echo(click.style("- User Feedback", fg="yellow"))
        configure_gemini_enterprise_for_fedramp_high(credentials, project_id, engine_id)
    elif compliance_regime == 'IL4':
        click.echo(click.style("Gemini Enterprise contains default features that are not yet authorized for IL4 and must be disabled. These features are currently:", fg="yellow"))
        click.echo(click.style("- Grounding with OneDrive / Google Drive File Uploads", fg="yellow"))
        click.echo(click.style("- Grounding with Google Search", fg="yellow"))
        click.echo(click.style("- Image / Video Generation", fg="yellow"))
        click.echo(click.style("- Implicit Model Data Caching", fg="yellow"))
        click.echo(click.style("- Knowledge Graph / People Connectors", fg="yellow"))
        click.echo(click.style("- Location Context", fg="yellow"))
        click.echo(click.style("- Memory and Customization", fg="yellow"))
        click.echo(click.style("- Model Armor", fg="yellow"))
        click.echo(click.style("- NotebookLM Enterprise", fg="yellow"))
        click.echo(click.style("- Prompt Gallery", fg="yellow"))
        click.echo(click.style("- Session Sharing", fg="yellow"))
        click.echo(click.style("- User Event Collection", fg="yellow"))
        click.echo(click.style("- User Feedback", fg="yellow"))
        configure_gemini_enterprise_for_il4(credentials, project_id, engine_id)
    elif compliance_regime == 'IL5':
        click.echo(click.style("Gemini Enterprise contains default features that are not yet authorized for IL5 and must be disabled. These features are currently:", fg="yellow"))
        click.echo(click.style("- Grounding with OneDrive / Google Drive File Uploads", fg="yellow"))
        click.echo(click.style("- Grounding with Google Search", fg="yellow"))
        click.echo(click.style("- Image / Video Generation", fg="yellow"))
        click.echo(click.style("- Implicit Model Data Caching", fg="yellow"))
        click.echo(click.style("- Knowledge Graph / People Connectors", fg="yellow"))
        click.echo(click.style("- Location Context", fg="yellow"))
        click.echo(click.style("- Memory and Customization", fg="yellow"))
        click.echo(click.style("- Model Armor", fg="yellow"))
        click.echo(click.style("- NotebookLM Enterprise", fg="yellow"))
        click.echo(click.style("- Prompt Gallery", fg="yellow"))
        click.echo(click.style("- Session Sharing", fg="yellow"))
        click.echo(click.style("- User Event Collection", fg="yellow"))
        click.echo(click.style("- User Feedback", fg="yellow"))
        configure_gemini_enterprise_for_il5(credentials, project_id, engine_id)

    click.echo(click.style("Compliance configuration complete!", fg='green'))

    # Get Widget Config ID to display
    config_id = get_widget_config_id(credentials, project_id, engine_id)
    click.echo(click.style(f"Gemini Enterprise Application ID: {engine_id}", fg='green'))
    click.echo(click.style(f"Gemini Enterprise Widget Config ID: {config_id}", fg='green'))


@app.command("update-idp")
@click.option('--project-id', required=True, help='GCP Project ID')
@click.option('--engine-id', required=True, help='Gemini Enterprise Engine ID')
@click.option('--workforce-pool-id', required=True, help='Workforce Identity Pool ID')
@click.option('--workforce-provider-id', required=True, help='Workforce Identity Provider ID')
def update_idp(project_id, engine_id, workforce_pool_id, workforce_provider_id):
    """Configures the Identity Provider for a Gemini Enterprise application widget."""
    credentials = get_credentials()
    configure_idp_for_widget(credentials, project_id, engine_id, workforce_pool_id, workforce_provider_id)


##############################################################
################       gem4gov datastore      ################
##############################################################

@cli.group()
def datastore():
    """Manage Gemini Enterprise data stores."""
    pass

@datastore.command("import")
@click.option('--project-id', required=True, help='GCP Project ID')
@click.option('--source-type', required=True, type=click.Choice(['gcs', 'bigquery']), help='Source of the documents to import')
@click.option('--data-store-id', required=False, help='Gemini Enterprise Data Store ID')
@click.option('--gcs-bucket', required=False, help='Optional GCS Bucket name to simplify the prompt')
def import_documents(project_id, source_type, data_store_id, gcs_bucket):
    """Import documents into a Gemini Enterprise data store."""
    credentials = get_credentials()
    
    # Set quota project
    credentials = credentials.with_quota_project(project_id)
    
    import_documents_helper(credentials, project_id, source_type, data_store_id, gcs_bucket)

##############################################################
################       gem4gov license        ################
##############################################################

@cli.group()
def license():
    """Manages Gemini for Government licenses."""
    pass

@license.command(name='list')
@click.option('--billing-account', required=True, help='The billing account ID.')
@click.option('--quota-project', required=False, help='The project ID to use for API quota.')
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='The output format.')
def list_licenses(billing_account, quota_project, format):
    """Lists available Gemini for Government license configurations for a billing account."""
    credentials = get_credentials()
    if quota_project:
        credentials = credentials.with_quota_project(quota_project)
        
    # Use discoveryengine v1alpha as per PDF
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)
    
    try:
        request = service.billingAccounts().billingAccountLicenseConfigs().list(
            parent=f'billingAccounts/{billing_account}'
        )
        response = request.execute()
        
        configs = response.get('billingAccountLicenseConfigs', [])
        
        if format == 'json':
            click.echo(json.dumps(configs, indent=2))
            return

        if not configs:
            click.echo(f"No license configurations found for billing account {billing_account}.")
            return

        for config in configs:
            name = config.get('subscriptionDisplayName', config.get('name'))
            total = config.get('licenseCount', 0)
            distributions = config.get('licenseConfigDistributions', {})
            distributed = sum(int(v) for v in distributions.values())
            available = int(total) - distributed
            
            # Extract ID from name: billingAccounts/ID/billingAccountLicenseConfigs/CONFIG_ID
            config_id = config.get('name').split('/')[-1]
            
            click.echo(f"Subscription: {name}")
            click.echo(f"  ID: {config_id}")
            click.echo(f"  Total Licenses: {total}")
            click.echo(f"  Distributed: {distributed}")
            click.echo(f"  Available: {available}")
            click.echo("---")
            
    except HttpError as e:
        click.echo(f"An error occurred: {e}")
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}")

@license.command(name='distribute')
@click.option('--billing-account', required=True, help='The billing account ID.')
@click.option('--config-id', required=True, help='The billing account license config ID.')
@click.option('--target-project-number', required=True, help='The target project number.')
@click.option('--location', default='global', type=click.Choice(['global', 'us', 'eu']), help='The location.')
@click.option('--count', required=True, type=int, help='The number of licenses to distribute (incremental).')
@click.option('--license-config-id', help='The existing project-level license config ID (optional).')
@click.option('--quota-project', required=False, help='The project ID to use for API quota.')
def distribute_licenses(billing_account, config_id, target_project_number, location, count, license_config_id, quota_project):
    """Distributes Gemini for Government licenses to a project."""
    credentials = get_credentials()
    if quota_project:
        credentials = credentials.with_quota_project(quota_project)
    
    endpoint = "https://discoveryengine.googleapis.com"
    if location == 'us':
        endpoint = "https://us-discoveryengine.googleapis.com"
    elif location == 'eu':
        endpoint = "https://eu-discoveryengine.googleapis.com"
        
    client_options = ClientOptions(api_endpoint=endpoint)
    # v1alpha is needed for billingAccountLicenseConfigs
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)
    
    name = f'billingAccounts/{billing_account}/billingAccountLicenseConfigs/{config_id}'
    
    body = {
        "projectNumber": target_project_number,
        "location": location,
        "licenseCount": count
    }
    if license_config_id:
        body["licenseConfigId"] = license_config_id

    try:
        request = service.billingAccounts().billingAccountLicenseConfigs().distributeLicenseConfig(
            name=name,
            body=body
        )
        response = request.execute()
        click.echo("Licenses distributed successfully!")
        click.echo(json.dumps(response, indent=2))
        
    except HttpError as e:
        click.echo(f"An error occurred: {e}")
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}")

##############################################################
################       gem4gov license        ################
##############################################################

@cli.group()
def license():
    """Manages Gemini for Government licenses."""
    pass

@license.command(name='list')
@click.option('--billing-account', required=True, help='The billing account ID.')
@click.option('--quota-project', required=False, help='The project ID to use for API quota.')
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='The output format.')
def list_licenses(billing_account, quota_project, format):
    """Lists available Gemini for Government license configurations for a billing account."""
    credentials = get_credentials()
    if quota_project:
        credentials = credentials.with_quota_project(quota_project)
        
    # Use discoveryengine v1alpha as per PDF
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)
    
    try:
        request = service.billingAccounts().billingAccountLicenseConfigs().list(
            parent=f'billingAccounts/{billing_account}'
        )
        response = request.execute()
        
        configs = response.get('billingAccountLicenseConfigs', [])
        
        if format == 'json':
            click.echo(json.dumps(configs, indent=2))
            return

        if not configs:
            click.echo(f"No license configurations found for billing account {billing_account}.")
            return

        for config in configs:
            name = config.get('subscriptionDisplayName', config.get('name'))
            total = config.get('licenseCount', 0)
            distributions = config.get('licenseConfigDistributions', {})
            distributed = sum(int(v) for v in distributions.values())
            available = int(total) - distributed
            
            # Extract ID from name: billingAccounts/ID/billingAccountLicenseConfigs/CONFIG_ID
            config_id = config.get('name').split('/')[-1]
            
            click.echo(f"Subscription: {name}")
            click.echo(f"  ID: {config_id}")
            click.echo(f"  Total Licenses: {total}")
            click.echo(f"  Distributed: {distributed}")
            click.echo(f"  Available: {available}")
            click.echo("---")
            
    except HttpError as e:
        click.echo(f"An error occurred: {e}")
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}")

@license.command(name='distribute')
@click.option('--billing-account', required=True, help='The billing account ID.')
@click.option('--config-id', required=True, help='The billing account license config ID.')
@click.option('--target-project-number', required=True, help='The target project number.')
@click.option('--location', default='global', type=click.Choice(['global', 'us', 'eu']), help='The location.')
@click.option('--count', required=True, type=int, help='The number of licenses to distribute (incremental).')
@click.option('--license-config-id', help='The existing project-level license config ID (optional).')
@click.option('--quota-project', required=False, help='The project ID to use for API quota.')
def distribute_licenses(billing_account, config_id, target_project_number, location, count, license_config_id, quota_project):
    """Distributes Gemini for Government licenses to a project."""
    credentials = get_credentials()
    if quota_project:
        credentials = credentials.with_quota_project(quota_project)
    
    endpoint = "https://discoveryengine.googleapis.com"
    if location == 'us':
        endpoint = "https://us-discoveryengine.googleapis.com"
    elif location == 'eu':
        endpoint = "https://eu-discoveryengine.googleapis.com"
        
    client_options = ClientOptions(api_endpoint=endpoint)
    # v1alpha is needed for billingAccountLicenseConfigs
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)
    
    name = f'billingAccounts/{billing_account}/billingAccountLicenseConfigs/{config_id}'
    
    body = {
        "projectNumber": target_project_number,
        "location": location,
        "licenseCount": count
    }
    if license_config_id:
        body["licenseConfigId"] = license_config_id

    try:
        request = service.billingAccounts().billingAccountLicenseConfigs().distributeLicenseConfig(
            name=name,
            body=body
        )
        response = request.execute()
        click.echo("Licenses distributed successfully!")
        click.echo(json.dumps(response, indent=2))
        
    except HttpError as e:
        click.echo(f"An error occurred: {e}")
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}")




def import_documents_helper(credentials, project_id, source_type, data_store_id=None, gcs_bucket=None):
    """Helper to import documents into a selected data store."""
    if not data_store_id:
        click.echo(nl=True)
        click.echo(click.style(f"Fetching available Gemini Enterprise data stores for import destination...", fg='yellow'))
        
        # List and select data store
        data_store_id = list_data_stores(credentials, project_id)
    
    if not data_store_id or data_store_id == 'none':
        click.echo("No data store selected. Exiting import process.")
        return

    # Validate data store exists
    click.echo(f"Inspecting data store: {data_store_id}...")
    ds_details = validate_data_store(credentials, project_id, data_store_id)
    
    if not ds_details.get('valid', False):
        click.echo(click.style(f"Data Store {data_store_id} could not be validated or does not exist.", fg='red'))
        if not click.confirm("Do you want to proceed anyway?"):
            return

    # Dispatch based on source-type
    if source_type == 'gcs':
        # GCS Data Store
        click.echo(click.style("Importing from Google Cloud Storage.", fg='green'))
        
        if gcs_bucket:
            relative_path = click.prompt(f'Please enter the path to the documents relative to the root of gs://{gcs_bucket}/ (leave blank for root)', type=str, default="").strip()
            bucket_name = gcs_bucket
            prefix = relative_path
        else:
            gcs_uri = click.prompt('Please enter the GCS URI to the documents (e.g., gs://my-bucket/path/to/docs)', type=str).strip()
            
            if not gcs_uri.startswith("gs://"):
                click.echo(click.style("Invalid URI. Must start with 'gs://'.", fg='red'))
                return

            # Parse bucket and prefix
            # gs://bucket/prefix...
            parts = gcs_uri[5:].split('/', 1)
            bucket_name = parts[0]
            prefix = parts[1] if len(parts) > 1 else ""
        
        # Let's clean the prefix
        prefix = prefix.strip('/')
        if prefix:
             path_prefix = f"{prefix}/**"
        else:
             path_prefix = "**"
        
        click.echo(f"Importing from: gs://{bucket_name}/{path_prefix}")
        
        if click.confirm("Proceed with import?"):
            import_gcs_documents(credentials, project_id, data_store_id, bucket_name, path_prefix)
            click.echo(click.style("Import operation started successfully.", fg='green'))
            
    elif source_type == 'bigquery':
        click.echo(click.style("BigQuery import via this command is not yet implemented.", fg='yellow'))
        click.echo("Please use the 'onboard' command for BigQuery data store creation and initial import.")


def create_application_logic(credentials, project_id, data_store_list, workforce_pool_id, workforce_provider_id, compliance_regime=None, engine_id=None, engine_display_name=None, company_name=None, enable_audit_logs=False):
    """Shared logic for creating a Gemini Enterprise application."""
    if not engine_display_name:
        engine_display_name = click.prompt('Please enter a Display Name for the Gemini Enterprise application').strip()
    if not company_name:
        company_name = click.prompt('Please enter the Agency / Department Name (no abbreviations)').strip()
    
    if not engine_id:
        click.echo(nl=True)
        import random
        import string
        engine_id = 'g4g-gem-ent-app-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    
    create_engine(credentials, project_id, engine_id, engine_display_name, company_name, data_store_list, enable_audit_logs)

    if workforce_pool_id and workforce_provider_id:
        configure_idp_for_widget(credentials, project_id, engine_id, workforce_pool_id, workforce_provider_id)
    
    # Re-using the prompt from onboard for consistency
    if not compliance_regime:
        click.echo(nl=True)
        click.echo("What compliance regime will this application be deployed in?")
        click.echo("1) FedRAMP High")
        click.echo("2) IL4")
        click.echo("3) IL5")
        click.echo("4) None")
        compliance_regime = click.prompt('Please enter the number for your response', type=click.Choice(['1', '2', '3', '4']), default = '1', show_default = False)

    if compliance_regime in ['1', 'FEDRAMP_HIGH']:
        click.echo(click.style("Configuring for FedRAMP High...", fg="yellow"))
        configure_gemini_enterprise_for_fedramp_high(credentials, project_id, engine_id)
    elif compliance_regime in ['2', 'IL4']:
        click.echo(click.style("Configuring for IL4...", fg="yellow"))
        configure_gemini_enterprise_for_il4(credentials, project_id, engine_id)
    elif compliance_regime in ['3', 'IL5']:
        click.echo(click.style("Configuring for IL5...", fg="yellow"))
        configure_gemini_enterprise_for_il5(credentials, project_id, engine_id)
    elif compliance_regime in ['4', 'NONE']:
        click.echo(click.style("Skipping compliance-specific app configuration...", fg="yellow"))

    click.echo(nl=True)
    
    config_id = get_widget_config_id(credentials, project_id, engine_id)

    click.echo(click.style("Application creation complete!", fg='green'))
    click.echo(click.style(f"Gemini Enterprise Application ID: {engine_id}", fg='green'))
    click.echo(click.style(f"Gemini Enterprise Widget Config ID: {config_id}", fg='green'))
    if data_store_list:
        click.echo(click.style(f"Gemini Enterprise Data Store IDs: {', '.join(data_store_list)}", fg='green'))
        for ds_id in data_store_list:
            click.echo(click.style(f"Data Store URL ({ds_id}): https://console.cloud.google.com/gen-app-builder/locations/us/engines/{engine_id}/collections/default_collection/data-stores/{ds_id}/data/documents?project={project_id}", fg='green'))
    
    click.echo(nl=True)
    click.echo(nl=True)

    if config_id:
        if workforce_pool_id and workforce_provider_id:
            # URL encode the continue URL
            import urllib.parse
            continue_url = f"https://vertexaisearch.cloud.google/us/home/cid/{config_id}"
            encoded_continue_url = urllib.parse.quote(continue_url, safe='')
            final_url = f"https://auth.cloud.google/signin/locations/global/workforcePools/{workforce_pool_id}/providers/{workforce_provider_id}?continueUrl={encoded_continue_url}&hl=en_US"
            click.echo(click.style(f"Gemini Enterprise UI URL: {final_url}", fg='green'))
        else:
            click.echo(click.style(f"Gemini Enterprise UI URL: https://vertexaisearch.cloud.google.com/us/home/cid/{config_id}?hl=en_US", fg='green'))
    
    click.echo(nl=True)
    click.echo(click.style("NOTE: Please wait approximately 10 minutes before using your Gemini Enterprise application as it finishes provisioning.", fg='yellow'))

    return engine_id, config_id

##############################################################
################ gem4gov CLI Helper Functions ################
##############################################################

def get_project_number(credentials, project_id):
    """Gets the project number for a given project ID."""
    try:
        service = build('cloudresourcemanager', 'v1', credentials=credentials)
        request = service.projects().get(projectId=project_id)
        response = request.execute()
        return response['projectNumber']
    except Exception as e:
        click.echo(f"An error occurred while getting the project number: {e}")
        return None


def check_apis(credentials, project_id):
    """Checks if the required APIs are enabled."""
    service = build('serviceusage', 'v1', credentials=credentials)
    
    required_apis = [
        'aiplatform.googleapis.com',
        'cloudresourcemanager.googleapis.com',
        'discoveryengine.googleapis.com',
        'iam.googleapis.com',
        'serviceusage.googleapis.com',
        'storage.googleapis.com',
        'bigquery.googleapis.com'
    ]

    enabled_apis = []
    disabled_apis = []

    for api in required_apis:
        request = service.services().get(name=f'projects/{project_id}/services/{api}')
        response = request.execute()
        if response['state'] == 'ENABLED':
            enabled_apis.append(api)
        else:
            disabled_apis.append(api)

    missing_required_apis = [api for api in required_apis if api not in enabled_apis]

    if missing_required_apis:
        click.echo("The following required APIs are not enabled:")
        for api in missing_required_apis:
            click.echo(f"- {api}")
        
        if click.confirm('Would you like to enable these missing APIs?'):
            enable_apis(credentials, project_id, missing_required_apis)
        else:
            click.echo("Exiting. Please enable the missing APIs and re-run the script.")
            click.echo(click.style("Exiting Onboarding process...", fg="red"))
            sys.exit(1)

    click.echo("All required APIs are enabled.")

    return True


def enable_apis(credentials, project_id, apis_to_enable):
    """Enable the specified APIs."""
    service = build('serviceusage', 'v1', credentials=credentials)
    for api in apis_to_enable:
        click.echo(f"Enabling {api}...")
        request = service.services().enable(
            name=f'projects/{project_id}/services/{api}'
        )
        try:
            # Adding a blank body to the request
            request.execute()
            click.echo(f"{api} enabled successfully.")
        except Exception as e:
            click.echo(f"An error occurred while enabling {api}: {e}")
            click.echo("Please try enabling the APIs manually and re-run the script.")
            click.echo(click.style("Exiting Onboarding process...", fg="red"))
            sys.exit(1)


def check_identity_provider(credentials, project_id):
    """Checks the identity provider configuration for the Gemini for Government project."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)
    
    try:
        request = service.projects().locations().getAclConfig(
            name=f'projects/{project_id}/locations/us/aclConfig'
        )
        response = request.execute()

        idp_config = response.get('idpConfig', {})
        idp_type = idp_config.get('idpType')

        if idp_type in ["GSUITE", "THIRD_PARTY"]:
            click.echo(f"Identity provider is already configured: {idp_type}")
        else:
            click.echo("Identity provider is not yet configured.")
        
        return idp_type

    except Exception as e:
        # If getAclConfig fails, it's likely not configured.
        click.echo(f"Error: {e}")
        click.echo("Identity provider is not yet configured.")
        return "IDP_TYPE_UNSPECIFIED"


def configure_identity_provider(credentials, project_id, idp_type, workforce_pool_id=None):
    """Configures the identity provider for the Gemini for Government project."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)
    
    if idp_type == '1':
        patch_body = {
            "idpConfig": {
                "idpType": "GSUITE"
            }
        }
    
    elif idp_type == '2':
        patch_body = {
            "idpConfig": {
                "idpType": "THIRD_PARTY",
                "externalIdpConfig": {
                    "workforcePoolName": f"locations/global/workforcePools/{workforce_pool_id}"
                }
            }
        }

    request = service.projects().locations().updateAclConfig(
        name=f'projects/{project_id}/locations/us/aclConfig',
        body=patch_body
    )

    try:
        response = request.execute()
        click.echo(f"Identity provider configured successfully.")
        if idp_type == '1':
            return "GSUITE"
        elif idp_type == '2':
            return "THIRD_PARTY"
    except Exception as e:
        click.echo(f"An error occurred while configuring the identity provider: {e}")
        click.echo(click.style("Exiting Onboarding process...", fg="red"))
        sys.exit(1)


def check_cmek(credentials, project_id):
    """Checks the CMEK configuration for the Gemini for Government project."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)
    
    try:
        request = service.projects().locations().getCmekConfig(
            name=f'projects/{project_id}/locations/us/cmekConfig'
        )
        response = request.execute()

        state = response.get('state', None)
        kms_key_name = response.get('kmsKey', None)

        if state == 'ACTIVE' and kms_key_name != None:
            click.echo(f'CMEK is configured for the "us" multi-region: {kms_key_name}')
        else:
            click.echo('CMEK is not yet configured for the "us" multi-region')
        
        return state

    except HttpError as e:
        if e.resp.status == 404:
            click.echo(click.style("CMEK is not yet configured.", fg="red"))
            return "STATE_UNSPECIFIED"
        else:
            click.echo(f"Error: {e}")
            click.echo("CMEK is not yet configured.")
            return "STATE_UNSPECIFIED"
    except Exception as e:
        # If getAclConfig fails, it's likely not configured.
        click.echo(f"Error: {e}")
        click.echo(click.style("CMEK is not yet configured.", fg="red"))
        return "STATE_UNSPECIFIED"


def validate_kms_key(credentials, kms_key_name):
    """Validates that a KMS key exists, is in the 'us' multi-region, and is symmetric."""
    try:
        service = build('cloudkms', 'v1', credentials=credentials)
        request = service.projects().locations().keyRings().cryptoKeys().get(name=kms_key_name)
        response = request.execute()

        # Validate the key's location
        if 'us' not in response['name']:
            click.echo(f"KMS key is not in the 'us' multi-region.")
            return False

        # Validate that the key is symmetric
        if response['purpose'] != 'ENCRYPT_DECRYPT' or 'GOOGLE_SYMMETRIC_ENCRYPTION' not in response.get('versionTemplate', {}).get('algorithm', ''):
            click.echo(f"KMS key is not a symmetric key.")
            return False

        click.echo("KMS key validated successfully.")
        return True

    except Exception as e:
        click.echo(f"An error occurred while validating the KMS key: {e}")
        return False


def grant_kms_permissions(credentials, kms_key_name, project_number):
    """Grants KMS permissions to the necessary service accounts."""
    try:
        service = build('cloudkms', 'v1', credentials=credentials)
        click.echo(f'Granting Discovery Engine and Cloud Storage Service Accounts the "Cloud KMS CryptoKey Encrypter/Decrypter" IAM role on the provided key.')
        # Get the current IAM policy
        request = service.projects().locations().keyRings().cryptoKeys().getIamPolicy(resource=kms_key_name)
        policy = request.execute()

        role = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
        members = [
            f"serviceAccount:service-{project_number}@gcp-sa-discoveryengine.iam.gserviceaccount.com",
            f"serviceAccount:service-{project_number}@gs-project-accounts.iam.gserviceaccount.com"
        ]

        # Check if the role already exists in the policy
        binding_found = False
        for binding in policy.get('bindings', []):
            if binding['role'] == role:
                binding_found = True
                # Add members to existing role binding if they are not already present
                for member in members:
                    if member not in binding['members']:
                        binding['members'].append(member)
                break
        
        if not binding_found:
            if 'bindings' not in policy:
                policy['bindings'] = []
            policy['bindings'].append({'role': role, 'members': members})

        # Set the new IAM policy
        body = {'policy': policy}
        request = service.projects().locations().keyRings().cryptoKeys().setIamPolicy(resource=kms_key_name, body=body)
        request.execute()

        click.echo(f"Successfully granted KMS permissions to Discovery Engine and Cloud Storage Service Accounts.")
        return True

    except Exception as e:
        click.echo(f"An error occurred while granting KMS permissions to Discovery Engine and Cloud Storage Service Accounts: {e}")
        return False


def configure_cmek(credentials, project_id, kms_key_name):
    """Configures the CMEK for the Gemini for Government project."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)
    
    patch_body = {
        "name": f"projects/{project_id}/locations/us/cmekConfig",
        "kmsKey": kms_key_name
    }

    request = service.projects().locations().updateCmekConfig(
        name=f'projects/{project_id}/locations/us/cmekConfig',
        body=patch_body
    )

    try:
        response = request.execute()
        click.echo(f"CMEK configured successfully.")
        return True
    
    except Exception as e:
        click.echo(f"An error occurred while configuring CMEK: {e}")
        click.echo(click.style("Exiting Onboarding process...", fg="red"))
        sys.exit(1)


def create_engine(credentials, project_id, engine_id, display_name, company_name, data_store_list, enable_audit_logs=False):
    """Creates a new engine."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)
    
    # Get the absolute path to the directory containing the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to the YAML file
    yaml_path = os.path.join(script_dir, 'engine_features.yaml')

    # Load features from the YAML file
    with open(yaml_path, 'r') as f:
        engine_features = yaml.safe_load(f)

    engine = {
        "displayName": display_name,
        "appType": "APP_TYPE_INTRANET",
        "solutionType": "SOLUTION_TYPE_SEARCH",
        "searchEngineConfig": {
            "searchTier": "SEARCH_TIER_ENTERPRISE",
            "searchAddOns": ["SEARCH_ADD_ON_LLM"],
            "requiredSubscriptionTier": "SUBSCRIPTION_TIER_SEARCH_AND_ASSISTANT"
        },
        "features": engine_features.get('features'),
        "industryVertical": "GENERIC",
        "disableAnalytics": True,
        "commonConfig": {
            "companyName": company_name
        },
        # "knowledgeGraphConfig": {
        #     "enablePrivateKnowledgeGraph": False,
        #     "featureConfig": {}
        # },
        # "privateKnowledgeGraphMetadata": {
        #     "privateKnowledgeGraphState": "ACTIVE"
        # },
        "sessionConfig": {
            "sessionManagementPolicy": "VERTEX_AI_MANAGED"
        },
        "disableCmekChanges": True,
        "dataStores": [],
        "dataStoreIds": []
    }

    if enable_audit_logs:
        engine["observabilityConfig"] = {
            "observabilityEnabled": True,
            "sensitiveLoggingEnabled": True
        }

    if data_store_list:
        engine['dataStoreIds'] = data_store_list
    else:
        engine['dataStoreIds'] = []

    request = service.projects().locations().collections().engines().create(
        parent=f'projects/{project_id}/locations/us/collections/default_collection',
        body=engine,
        engineId=engine_id
    )

    try:
        response = request.execute()
        
        # Check if response is an Operation (LRO)
        if 'name' in response and 'operations' in response['name']:
             click.echo(f"Engine creation initiated. Waiting for Engine to be ready...")
             
             engine_full_name = f"projects/{project_id}/locations/us/collections/default_collection/engines/{engine_id}"
             
             while True:
                try:
                    # Poll the Engine resource directly
                    eng_request = service.projects().locations().collections().engines().get(name=engine_full_name)
                    eng_response = eng_request.execute()
                    
                    # If we get here, the engine exists.
                    click.echo("Engine created successfully!")
                    break
                except HttpError as e:
                    if e.resp.status == 404:
                        # Not found yet, keep waiting
                        click.echo(".", nl=False)
                        time.sleep(5)
                    else:
                        raise e
             click.echo(nl=True)
        else:
             # If it's not an operation or already done (unlikely for create)
             click.echo(f"Engine created successfully!")

    except Exception as e:
        click.echo("Received an API error during creation. Checking if engine was created asynchronously despite the error...")
        engine_full_name = f"projects/{project_id}/locations/us/collections/default_collection/engines/{engine_id}"
        max_retries = 12
        for attempt in range(max_retries):
            try:
                eng_request = service.projects().locations().collections().engines().get(name=engine_full_name)
                eng_response = eng_request.execute()
                click.echo("Engine verified successfully! Proceeding with configuration.")
                return
            except Exception as inner_e:
                if attempt < max_retries - 1:
                    click.echo(".", nl=False)
                    time.sleep(5)
                else:
                    click.echo(f"\nAn error occurred while creating the engine: {e}")
                    click.echo(click.style("Exiting Onboarding process...", fg="red"))
                    sys.exit(1)


def configure_idp_for_widget(credentials, project_id, engine_id, workforce_pool_id, workforce_provider_id):
    """Configures the identity provider for the default search widget."""
    try:
        # Get access token
        token_process = subprocess.run(['gcloud', 'auth', 'print-access-token'], check=True, capture_output=True, text=True)
        access_token = token_process.stdout.strip()

        workforce_identity_pool_provider = f"locations/global/workforcePools/{workforce_pool_id}/providers/{workforce_provider_id}"
        
        url = (
            f"https://us-discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/us/collections/default_collection/"
            f"engines/{engine_id}/widgetConfigs/default_search_widget_config?updateMask=accessSettings"
        )
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "x-goog-user-project": project_id,
            "Content-Type": "application/json"
        }
        
        data = {
            "accessSettings": {
                "enableWebApp": True,
                "workforceIdentityPoolProvider": workforce_identity_pool_provider
            }
        }
        
        # Use subprocess to run the curl command
        curl_command = [
            'curl', '-X', 'PATCH',
            '-H', f"Authorization: Bearer {access_token}",
            '-H', f"x-goog-user-project: {project_id}",
            '-H', "Content-Type: application/json",
            '-d', json.dumps(data),
            url
        ]


        # Retry logic for widget config availability
        max_retries = 5
        for attempt in range(max_retries):
            result = subprocess.run(curl_command, capture_output=True, text=True)
            
            if result.returncode == 0 and "error" not in result.stdout.lower():
                click.echo("Successfully configured identity provider for the search widget.")

                break
            

            
            if attempt < max_retries - 1:
                click.echo("Waiting for widget config to be ready...", nl=False)
                time.sleep(5)
                click.echo(nl=True)
        else:
            click.echo(f"An error occurred while configuring the identity provider for the search widget after {max_retries} attempts:")
            click.echo(result.stderr)
            click.echo(result.stdout)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        click.echo(f"An error occurred: {e}")
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}")


def disable_user_event_collection(credentials, project_id, engine_id):
    """Disables user event collection for the default search widget."""
    try:
        # Get access token
        token_process = subprocess.run(['gcloud', 'auth', 'print-access-token'], check=True, capture_output=True, text=True)
        access_token = token_process.stdout.strip()

        url = (
            f"https://us-discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/us/collections/default_collection/"
            f"engines/{engine_id}/widgetConfigs/default_search_widget_config?updateMask=uiSettings.disableUserEventsCollection"
        )
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "x-goog-user-project": project_id,
            "Content-Type": "application/json"
        }
        
        data = {
            "uiSettings": {
                "disableUserEventsCollection": True
            }
        }
        
        # Use subprocess to run the curl command
        curl_command = [
            'curl', '-X', 'PATCH',
            '-H', f"Authorization: Bearer {access_token}",
            '-H', f"x-goog-user-project: {project_id}",
            '-H', "Content-Type: application/json",
            '-d', json.dumps(data),
            url
        ]


        # Retry logic for widget config availability
        max_retries = 5
        for attempt in range(max_retries):
            result = subprocess.run(curl_command, capture_output=True, text=True)
            
            if result.returncode == 0 and "error" not in result.stdout.lower():
                click.echo("Successfully disabled user event collection.")

                break
            
            if attempt < max_retries - 1:
                click.echo("Waiting for widget config to be ready...", nl=False)
                time.sleep(5)
                click.echo(nl=True)
        else:
            click.echo(f"An error occurred while disabling user event collection after {max_retries} attempts:")
            click.echo(result.stderr)
            click.echo(result.stdout)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        click.echo(f"An error occurred: {e}")
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}")


def configure_gemini_enterprise_for_fedramp_high(credentials, project_id, engine_id):
    """Configures the Gemini Enterprise engine and default assistant for FedRAMP High."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)

    # Get the absolute path to the directory containing the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to the YAML file
    yaml_path = os.path.join(script_dir, 'engine_features.yaml')

    # Load features from the YAML file
    with open(yaml_path, 'r') as f:
        engine_features = yaml.safe_load(f)
    
    # Engine: Update FRH authorized features and disable Private Knowledge Graph (People Connectors are not yet authorized for FRH)
    engine_name = f"projects/{project_id}/locations/us/collections/default_collection/engines/{engine_id}"
    engine_patch_body = {
        "features": engine_features.get('features'),
        "disableAnalytics": True
    }
    engine_update_mask = "features"

    engine_request = service.projects().locations().collections().engines().patch(
        name=engine_name,
        body=engine_patch_body,
        updateMask=engine_update_mask
    )

    try:
        engine_response = engine_request.execute()
        click.echo(f"Engine {engine_id} configured for FedRAMP High.")
    except Exception as e:
        click.echo(f"An error occurred while configuring the engine for FedRAMP High: {e}")
        # Do not exit, as this may not be a critical failure.

    # Default Search Widget: Disable User Event Collection
    disable_user_event_collection(credentials, project_id, engine_id)

    # Assistant: Disable Grounding with Google Search / Location Context
    assistant_name = f"projects/{project_id}/locations/us/collections/default_collection/engines/{engine_id}/assistants/default_assistant"
    
    # Get access token
    try:
        token_process = subprocess.run(['gcloud', 'auth', 'print-access-token'], check=True, capture_output=True, text=True)
        access_token = token_process.stdout.strip()
    except subprocess.CalledProcessError as e:
        click.echo(f"Error getting access token not critical, but noted: {e}")
        # We might not be able to proceed with curl if token fails, but let's try to continue or just return
        # If we can't get a token, we can't do the rest.
        # But user said "gracefully log... but continue". 
        # Continuing without a token will just fail the next step. 
        # I'll let it fail naturally or just return from this function logic?
        # Actually proper "continue" means try the next steps. 
        # If token fails, curl calls WILL fail. 
        pass
        access_token = ""

    if access_token:
        url = f"https://us-discoveryengine.googleapis.com/v1alpha/{assistant_name}?updateMask=customerPolicy,agentConfigs,generationConfig,disableLocationContext,webGroundingType,defaultWebGroundingToggleOff"

        assistant_patch_body = {
          "displayName":"Default Assistant",
          "googleSearchGroundingEnabled": False,
          "webGroundingType":"WEB_GROUNDING_TYPE_ENTERPRISE_WEB_SEARCH",
          "customerPolicy":{
            "bannedPhrases":[]
          },
          "generationConfig":{
            "systemInstruction":{
              "additionalSystemInstruction":""
            }
          },
          "defaultWebGroundingToggleOff": False,
          "disableLocationContext": True
        }

        # Use subprocess to run the curl command
        curl_command = [
            'curl', '-X', 'PATCH',
            '-H', f"Authorization: Bearer {access_token}",
            '-H', f"x-goog-user-project: {project_id}",
            '-H', "Content-Type: application/json",
            '-d', json.dumps(assistant_patch_body),
            url
        ]

        try:
            result = subprocess.run(curl_command, capture_output=True, text=True)
            
            if result.returncode == 0 and "error" not in result.stdout.lower():
                 click.echo(f"Default assistant for engine {engine_id} configured for FedRAMP High.")
            else:
                 click.echo(f"An error occurred while configuring the default assistant for FedRAMP High:")
                 click.echo(result.stderr)
                 click.echo(result.stdout)
                 # Do not exit

        except Exception as e:
            click.echo(f"An error occurred while configuring the default assistant for FedRAMP High: {e}")
            # Do not exit

    # Project: Disable Implicit Model Caching
    try:
        aiplatform_client_options = ClientOptions(api_endpoint="https://us-central1-aiplatform.googleapis.com")
        aiplatform_service = build('aiplatform', 'v1', credentials=credentials, client_options=aiplatform_client_options)
        
        cache_config_name = f"projects/{project_id}/cacheConfig"
        cache_config_body = {
            "name": cache_config_name,
            "disableCache": True
        }

        request = aiplatform_service.projects().updateCacheConfig(
            name=cache_config_name,
            body=cache_config_body
        )
        request.execute()
        click.echo("Successfully disabled Implicit Model Caching for the project.")
    except Exception as e:
        click.echo(f"An error occurred while disabling Implicit Model Caching: {e}")
        # Do not exit, as this may not be a critical failure.


def configure_gemini_enterprise_for_il4(credentials, project_id, engine_id):
    """Configures the Gemini Enterprise engine and default assistant for IL4."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)

    # Get the absolute path to the directory containing the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to the YAML file
    yaml_path = os.path.join(script_dir, 'engine_features.yaml')

    # Load features from the YAML file
    with open(yaml_path, 'r') as f:
        engine_features = yaml.safe_load(f)
    
    # Engine: Update IL4 authorized features and disable Private Knowledge Graph (People Connectors are not yet authorized for IL4)
    engine_name = f"projects/{project_id}/locations/us/collections/default_collection/engines/{engine_id}"
    engine_patch_body = {
        "features": engine_features.get('features'),
        "disableAnalytics": True
    }
    engine_update_mask = "features"

    engine_request = service.projects().locations().collections().engines().patch(
        name=engine_name,
        body=engine_patch_body,
        updateMask=engine_update_mask
    )

    try:
        engine_response = engine_request.execute()
        click.echo(f"Engine {engine_id} configured for IL4.")
    except Exception as e:
        click.echo(f"An error occurred while configuring the engine for IL4: {e}")
        click.echo(click.style("Exiting Onboarding process...", fg="red"))
        sys.exit(1)

    # Default Search Widget: Disable User Event Collection
    disable_user_event_collection(credentials, project_id, engine_id)

    # Assistant: Disable Grounding with Google Search / Location Context
    assistant_name = f"projects/{project_id}/locations/us/collections/default_collection/engines/{engine_id}/assistants/default_assistant"
    
    # Get access token
    try:
        token_process = subprocess.run(['gcloud', 'auth', 'print-access-token'], check=True, capture_output=True, text=True)
        access_token = token_process.stdout.strip()
    except subprocess.CalledProcessError as e:
        click.echo(f"Error getting access token: {e}")
        click.echo(click.style("Exiting Onboarding process...", fg="red"))
        sys.exit(1)

    url = f"https://us-discoveryengine.googleapis.com/v1alpha/{assistant_name}?updateMask=generationConfig.defaultLanguage,webGroundingType,defaultWebGroundingToggleOff,enableEndUserAgentCreation,disableLocationContext"

    assistant_patch_body = {
        "generationConfig": {
            "defaultLanguage": "en"
        },
        "webGroundingType": "WEB_GROUNDING_TYPE_ENTERPRISE_WEB_SEARCH",
        "defaultWebGroundingToggleOff": False,
        "enableEndUserAgentCreation": False,
        "disableLocationContext": True
    }

    # Use subprocess to run the curl command
    curl_command = [
        'curl', '-X', 'PATCH',
        '-H', f"Authorization: Bearer {access_token}",
        '-H', f"x-goog-user-project: {project_id}",
        '-H', "Content-Type: application/json",
        '-d', json.dumps(assistant_patch_body),
        url
    ]

    try:
        result = subprocess.run(curl_command, capture_output=True, text=True)
        
        if result.returncode == 0 and "error" not in result.stdout.lower():
             click.echo(f"Default assistant for engine {engine_id} configured for IL4.")
        else:
             click.echo(f"An error occurred while configuring the default assistant for IL4:")
             click.echo(result.stderr)
             click.echo(result.stdout)
             click.echo(click.style("Exiting Onboarding process...", fg="red"))
             sys.exit(1)

    except Exception as e:
        click.echo(f"An error occurred while configuring the default assistant for IL4: {e}")
        click.echo(click.style("Exiting Onboarding process...", fg="red"))
        sys.exit(1)

    # Project: Disable Implicit Model Caching
    try:
        aiplatform_client_options = ClientOptions(api_endpoint="https://us-central1-aiplatform.googleapis.com")
        aiplatform_service = build('aiplatform', 'v1', credentials=credentials, client_options=aiplatform_client_options)
        
        cache_config_name = f"projects/{project_id}/cacheConfig"
        cache_config_body = {
            "name": cache_config_name,
            "disableCache": True
        }

        request = aiplatform_service.projects().updateCacheConfig(
            name=cache_config_name,
            body=cache_config_body
        )
        request.execute()
        click.echo("Successfully disabled Implicit Model Caching for the project.")
    except Exception as e:
        click.echo(f"An error occurred while disabling Implicit Model Caching: {e}")
        # Do not exit, as this may not be a critical failure.


def configure_gemini_enterprise_for_il5(credentials, project_id, engine_id):
    """Configures the Gemini Enterprise engine and default assistant for IL5."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)

    # Get the absolute path to the directory containing the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to the YAML file
    yaml_path = os.path.join(script_dir, 'engine_features.yaml')

    # Load features from the YAML file
    with open(yaml_path, 'r') as f:
        engine_features = yaml.safe_load(f)
    
    # Engine: Update IL5 authorized features and disable Private Knowledge Graph (People Connectors are not yet authorized for IL5)
    engine_name = f"projects/{project_id}/locations/us/collections/default_collection/engines/{engine_id}"
    engine_patch_body = {
        "features": engine_features.get('features'),
        "disableAnalytics": True
    }
    engine_update_mask = "features"

    engine_request = service.projects().locations().collections().engines().patch(
        name=engine_name,
        body=engine_patch_body,
        updateMask=engine_update_mask
    )

    try:
        engine_response = engine_request.execute()
        click.echo(f"Engine {engine_id} configured for IL5.")
    except Exception as e:
        click.echo(f"An error occurred while configuring the engine for IL5: {e}")
        click.echo(click.style("Exiting Onboarding process...", fg="red"))
        sys.exit(1)

    # Default Search Widget: Disable User Event Collection
    disable_user_event_collection(credentials, project_id, engine_id)

    # Assistant: Disable Grounding with Google Search / Location Context
    assistant_name = f"projects/{project_id}/locations/us/collections/default_collection/engines/{engine_id}/assistants/default_assistant"
    
    # Get access token
    try:
        token_process = subprocess.run(['gcloud', 'auth', 'print-access-token'], check=True, capture_output=True, text=True)
        access_token = token_process.stdout.strip()
    except subprocess.CalledProcessError as e:
        click.echo(f"Error getting access token: {e}")
        click.echo(click.style("Exiting Onboarding process...", fg="red"))
        sys.exit(1)

    url = f"https://us-discoveryengine.googleapis.com/v1alpha/{assistant_name}?updateMask=generationConfig.defaultLanguage,webGroundingType,defaultWebGroundingToggleOff,enableEndUserAgentCreation,disableLocationContext"

    assistant_patch_body = {
        "generationConfig": {
            "defaultLanguage": "en"
        },
        "webGroundingType": "WEB_GROUNDING_TYPE_ENTERPRISE_WEB_SEARCH",
        "defaultWebGroundingToggleOff": False,
        "enableEndUserAgentCreation": False,
        "disableLocationContext": True
    }

    # Use subprocess to run the curl command
    curl_command = [
        'curl', '-X', 'PATCH',
        '-H', f"Authorization: Bearer {access_token}",
        '-H', f"x-goog-user-project: {project_id}",
        '-H', "Content-Type: application/json",
        '-d', json.dumps(assistant_patch_body),
        url
    ]

    try:
        result = subprocess.run(curl_command, capture_output=True, text=True)
        
        if result.returncode == 0 and "error" not in result.stdout.lower():
             click.echo(f"Default assistant for engine {engine_id} configured for IL5.")
        else:
             click.echo(f"An error occurred while configuring the default assistant for IL5:")
             click.echo(result.stderr)
             click.echo(result.stdout)
             click.echo(click.style("Exiting Onboarding process...", fg="red"))
             sys.exit(1)

    except Exception as e:
        click.echo(f"An error occurred while configuring the default assistant for IL5: {e}")
        click.echo(click.style("Exiting Onboarding process...", fg="red"))
        sys.exit(1)

    # Project: Disable Implicit Model Caching
    try:
        aiplatform_client_options = ClientOptions(api_endpoint="https://us-central1-aiplatform.googleapis.com")
        aiplatform_service = build('aiplatform', 'v1', credentials=credentials, client_options=aiplatform_client_options)
        
        cache_config_name = f"projects/{project_id}/cacheConfig"
        cache_config_body = {
            "name": cache_config_name,
            "disableCache": True
        }

        request = aiplatform_service.projects().updateCacheConfig(
            name=cache_config_name,
            body=cache_config_body
        )
        request.execute()
        click.echo("Successfully disabled Implicit Model Caching for the project.")
    except Exception as e:
        click.echo(f"An error occurred while disabling Implicit Model Caching: {e}")
        # Do not exit, as this may not be a critical failure.


def get_widget_config_id(credentials, project_id, engine_id):
    """Gets the config ID for the default search widget."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)

    request = service.projects().locations().collections().engines().widgetConfigs().get(
        name=f'projects/{project_id}/locations/us/collections/default_collection/engines/{engine_id}/widgetConfigs/default_search_widget_config'
    )

    try:
        response = request.execute()
        config_id = response['configId']
        return config_id
    except Exception as e:
        click.echo(f"An error occurred while getting the widget config ID: {e}")
        return None

if __name__ == '__main__':
    cli()
