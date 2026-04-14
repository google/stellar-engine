# Copyright 2026 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import click
import json
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google.api_core.client_options import ClientOptions
import random
import string
import json

def generate_id(prefix):
    """Generates a random 6-character alphanumeric string."""
    return prefix + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))


def validate_data_store(credentials, project_id, data_store_id):
    """Validates existing Cloud Storage and BigQuery data stores."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)

    valid_response = {}

    try:
        request = service.projects().locations().dataStores().get(
            name=f'projects/{project_id}/locations/us/dataStores/{data_store_id}'
        )
        data_store = request.execute()
    except Exception as e:
        click.echo(click.style(f"An error occurred while validating data store {data_store_id}: {parse_http_error(e)}", fg=(255,165,0)))
        valid_response = {
            "valid": False,
            "id": data_store_id
        }
        return valid_response
    
    try:
        # Parse attributes from data store used for validation
        name = data_store.get('name', None)
        id = name.split('/')[-1]
        display_name = data_store.get('displayName', None)
        industry_vertical = data_store.get('industryVertical', None)
        solution_types = data_store.get('solutionTypes', [])
        kms_key_name = data_store.get('cmekConfig', {}).get('kmsKey', None)
        idp_type = data_store.get('idpConfig', {}).get('idpType', None)
        acl_enabled = data_store.get('aclEnabled', False)
        content_config = data_store.get('contentConfig', None)

        if industry_vertical == 'GENERIC':
            valid_response = {
                "valid": True,
                "name": name,
                "id": id,
                "display_name": display_name,
                "industry_vertical": industry_vertical,
                "solution_types": solution_types,
                "kms_key_name": kms_key_name,
                "idp_type": idp_type,
                "acl_enabled": acl_enabled,
                "content_config": content_config
            }
        else:
            valid_response = {
                "valid": False,
                "name": name,
                "id": id,
                "display_name": display_name,
                "industry_vertical": industry_vertical,
                "solution_types": solution_types,
                "kms_key_name": kms_key_name,
                "idp_type": idp_type,
                "acl_enabled": acl_enabled,
                "content_config": content_config
            }
        return valid_response

    except Exception as e:
        click.echo(click.style(f"An error occurred while validating data store {data_store_id}: {parse_http_error(e)}", fg=(255,165,0)))
        # Defaulting to create new flow
        valid_response = {
            "valid": False,
            "id": data_store_id
        }
        return valid_response
    

def list_data_stores(credentials, project_id):
    """Lists existing Cloud Storage and BigQuery data stores."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)

    try:
        request = service.projects().locations().dataStores().list(
            parent=f'projects/{project_id}/locations/us'
        )
        response = request.execute()
        data_stores = response.get('dataStores', [])

        valid_data_stores = []
        if data_stores:
            valid_data_stores = [ds for ds in data_stores if "SOLUTION_TYPE_SEARCH" in ds.get("solutionTypes", [])]

        if valid_data_stores:
            click.echo("Select a data store:")
            for i, ds in enumerate(valid_data_stores):
                click.echo(f"{i + 1}) {ds['displayName']} ({ds['name'].split('/')[-1]})")

        choice = click.prompt(
            'Please enter the number for your response',
            type=click.IntRange(1, len(valid_data_stores))
        )

        if choice <= len(valid_data_stores):
            return valid_data_stores[choice - 1]['name'].split('/')[-1]
        else: # invalid choice
            return None

    except Exception as e:
        click.echo(click.style(f"An error occurred while listing data stores: {parse_http_error(e)}", fg=(255,165,0)))
        # Defaulting to create new flow
        return None


def create_gcs_data_store(credentials, project_id, data_store_id, display_name):
    """Creates a new data store."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)
    
    data_store = {
        "displayName": display_name,
        "industryVertical": "GENERIC",
        "solutionTypes": ["SOLUTION_TYPE_SEARCH"],
        "contentConfig": "CONTENT_REQUIRED",
        "documentProcessingConfig": {
            "defaultParsingConfig": {
                "layoutParsingConfig": {
                    "enableTableAnnotation": True,
                    "enableImageAnnotation": True
                }
            },
            "chunkingConfig": {
                "layoutBasedChunkingConfig": {
                    "includeAncestorHeadings": True,
                    "chunkSize": 500
                }
            },
        },
    }

    request = service.projects().locations().collections().dataStores().create(
        parent=f"projects/{project_id}/locations/us/collections/default_collection",
        body=data_store,
        dataStoreId=data_store_id
    )
    
    try:
        response = request.execute()
        click.echo(f"Data store created successfully: {response['name']}")
    except Exception as e:
        click.echo(click.style(f"An error occurred while creating the data store: {parse_http_error(e)}", fg=(255,165,0)))
        exit()


def import_gcs_documents(credentials, project_id, data_store_id, gcs_bucket, path_prefix):
    """Imports documents into the data store."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)
    
    import_request = {
        "reconciliationMode": "FULL",
        "gcsSource": {
            "inputUris": [f"gs://{gcs_bucket}/{path_prefix}"],
            "dataSchema": "content"
        }
    }

    request = service.projects().locations().collections().dataStores().branches().documents().import_(
        parent=f'projects/{project_id}/locations/us/collections/default_collection/dataStores/{data_store_id}/branches/default_branch',
        body=import_request
    )

    try:
        response = request.execute()
        click.echo(f"Document import started. Operation: {response['name']}")
    except Exception as e:
        click.echo(click.style(f"An error occurred while importing documents: {parse_http_error(e)}", fg=(255,165,0)))
        exit()


def get_bq_schema(credentials, project_id, dataset_id, table_id):
    """Gets the schema of a BigQuery table."""
    service = build('bigquery', 'v2', credentials=credentials)
    try:
        request = service.tables().get(
            projectId=project_id,
            datasetId=dataset_id,
            tableId=table_id
        )
        response = request.execute()
        click.echo(f"Successfully retrieved schema for table {project_id}.{dataset_id}.{table_id}")
        return response.get('schema')
    except Exception as e:
        click.echo(click.style(f"An error occurred while getting the BigQuery table schema: {parse_http_error(e)}", fg=(255,165,0)))
        return None


def transform_bq_schema(bq_schema, key_properties):
    """Transforms a BigQuery schema to a Discovery Engine JSON schema."""
    
    def get_json_type(bq_type):
        if bq_type in ['INTEGER', 'INT64']:
            return 'integer'
        elif bq_type in ['FLOAT', 'FLOAT64', 'NUMERIC', 'BIGNUMERIC']:
            return 'number'
        elif bq_type in ['BOOLEAN', 'BOOL']:
            return 'boolean'
        return 'string'

    def transform_fields(fields):
        properties = {}
        for field in fields:
            field_name = field.get('name')
            if field.get('type') in ['RECORD', 'STRUCT']:
                property_definition = {
                    'type': 'object',
                    'properties': transform_fields(field.get('fields', []))
                }
            else:
                property_type = get_json_type(field.get('type'))
                
                if field_name in key_properties.values():
                    property_definition = {
                        'type': property_type,
                        'retrievable': True if property_type in ['number', 'string', 'boolean', 'integer', 'datetime', 'geolocation'] else False,
                        'keyPropertyMapping': [key for key, val in key_properties.items() if val == field_name][0]
                    }
                else:
                    property_definition = {
                        'type': property_type,
                        'searchable': True if property_type == 'string' else False,
                        'indexable': True if property_type in ['number', 'string', 'boolean', 'integer', 'datetime', 'geolocation'] else False,
                        'retrievable': True if property_type in ['number', 'string', 'boolean', 'integer', 'datetime', 'geolocation'] else False
                    }

            if field.get('mode') == 'REPEATED':
                properties[field_name] = {
                    'type': 'array',
                    'items': property_definition
                }
            else:
                properties[field_name] = property_definition

        return properties

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": transform_fields(bq_schema.get('fields', []))
    }


def create_bq_data_store(credentials, project_id, data_store_id, display_name, dataset_id, table_id):
    """Creates a new BigQuery data store."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)

    data_store = {
        "displayName": display_name,
        "industryVertical": "GENERIC",
        "solutionTypes": ["SOLUTION_TYPE_SEARCH"]
    }

    request = service.projects().locations().collections().dataStores().create(
        parent=f"projects/{project_id}/locations/us/collections/default_collection",
        body=data_store,
        dataStoreId=data_store_id
    )

    try:
        response = request.execute()
        click.echo(f"Data store created successfully: {response['name']}")
    except Exception as e:
        click.echo(click.style(f"An error occurred while creating the data store: {parse_http_error(e)}", fg=(255,165,0)))
        exit()


def create_data_store_schema(credentials, project_id, data_store_id, schema):
    """Patches the default schema with the BigQuery table schema. """
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)

    request = service.projects().locations().dataStores().schemas().patch(
        name=f'projects/{project_id}/locations/us/dataStores/{data_store_id}/schemas/default_schema',
        body={'jsonSchema': json.dumps(schema)}
    )

    try:
        response = request.execute()
        click.echo(f"Default schema for data store {data_store_id} successfully patched")
    except Exception as e:
        click.echo(click.style(f"An error occurred while patching the default schema: {parse_http_error(e)}", fg=(255,165,0)))
        exit()


def import_bq_documents(credentials, project_id, data_store_id, dataset_id, table_id, id_property):
    """Imports documents from a BigQuery table into the data store."""
    client_options = ClientOptions(api_endpoint="https://us-discoveryengine.googleapis.com")
    service = build('discoveryengine', 'v1alpha', credentials=credentials, client_options=client_options)

    import_request = {
        "reconciliationMode": "FULL",
        "bigquerySource": {
            "projectId": project_id,
            "datasetId": dataset_id,
            "tableId": table_id,
            "dataSchema": "custom"
        }
    }

    if id_property == 'auto':
        import_request['autoGenerateIds'] = True
    else:
        import_request['idField'] = id_property['id']

    request = service.projects().locations().collections().dataStores().branches().documents().import_(
        parent=f'projects/{project_id}/locations/us/collections/default_collection/dataStores/{data_store_id}/branches/default_branch',
        body=import_request
    )

    try:
        response = request.execute()
        click.echo(f"Document import started. Operation: {response['name']}")
    except Exception as e:
        click.echo(click.style(f"An error occurred while importing documents: {parse_http_error(e)}", fg=(255,165,0)))
        exit()


def parse_http_error(error: HttpError) -> str:
    """
    Parses an HttpError exception to extract the error message.

    Args:
        error: The HttpError exception object.

    Returns:
        A string containing the detailed error message.
    """
    try:
        error_details = json.loads(error.content.decode('utf-8'))
        message = error_details.get('error', {}).get('message', 'No error message found.')
        return message
    except (json.JSONDecodeError, AttributeError):
        # Fallback if content is not JSON or not in the expected format
        return str(error)