import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Inventory')

def lambda_handler(event, context):
    try:
        print("Full event received:", json.dumps(event, indent=2))
        
        # Handle both API Gateway calls and Lambda console testing
        location_id = None
        
        # If this is Lambda console test with default event
        if event.get('key1') == 'value1' and event.get('key2') == 'value2':
            print("Lambda console test detected - using location 100")
            location_id = "100"  # Use a default location for testing
        
        # If this is from API Gateway with Proxy Integration
        elif event.get('pathParameters') and event['pathParameters'].get('id'):
            location_id = event['pathParameters']['id']
            print(f"API Gateway call with location ID: {location_id}")
        
        # If this is from API Gateway without Proxy Integration (mapping template)
        elif event.get('id'):
            location_id = event.get('id')
            print(f"API Gateway call with location ID: {location_id}")
        
        # If testing directly in Lambda console with specific location
        elif event.get('location_id'):
            location_id = event.get('location_id')
            print(f"Direct test with location ID: {location_id}")
        
        if not location_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Location ID is required',
                    'usage': 'Send GET request to: /location/LOCATION-ID',
                    'example': '/location/100'
                })
            }
        
        print(f"Searching for items in location: {location_id}")
        
        # Convert location_id to integer
        try:
            location_id_int = int(location_id)
        except ValueError:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Location ID must be a number'})
            }
        
        # Query using the Global Secondary Index (LocationIndex)
        response = table.query(
            IndexName='LocationIndex',
            KeyConditionExpression=Key('location_id').eq(location_id_int)
        )
        
        items = response.get('Items', [])
        
        # Custom JSON encoder to handle Decimal objects
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj) if obj % 1 != 0 else int(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        print(f"Found {len(items)} items in location {location_id}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(items, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Failed to retrieve location inventory: {str(e)}'})
        }