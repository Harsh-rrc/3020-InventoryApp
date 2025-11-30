import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Inventory')

def lambda_handler(event, context):
    try:
        print("Full event received:", json.dumps(event, indent=2))
        
        # Extract item_id from the event
        item_id = None
        
        # If this is from API Gateway with Proxy Integration
        if event.get('pathParameters') and event['pathParameters'].get('id'):
            item_id = event['pathParameters']['id']
            print(f"API Gateway call with ID: {item_id}")
        
        # If this is from API Gateway without Proxy Integration (mapping template)
        elif event.get('id'):
            item_id = event.get('id')
            print(f"API Gateway call with ID: {item_id}")
        
        # If testing directly in Lambda console with specific ID
        elif event.get('item_id'):
            item_id = event.get('item_id')
            print(f"Direct test with ID: {item_id}")
        
        # If Lambda console test with default event, find an existing item
        elif event.get('key1') == 'value1' and event.get('key2') == 'value2':
            print("Lambda console test detected - finding an existing item")
            scan_response = table.scan()
            existing_items = scan_response.get('Items', [])
            
            if existing_items:
                item_id = existing_items[0]['item_id']
                print(f"Using existing item: {item_id}")
            else:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'No items found in database'})
                }
        
        if not item_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Item ID is required',
                    'usage': 'Send GET request to: /item/YOUR-ITEM-ID'
                })
            }
        
        print(f"Searching for item: {item_id}")
        
        # Query the table for the specific item
        response = table.query(
            KeyConditionExpression=Key('item_id').eq(item_id)
        )
        
        items = response.get('Items', [])
        
        # Custom JSON encoder to handle Decimal objects
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj) if obj % 1 != 0 else int(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        if not items:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Item not found in database',
                    'item_id': item_id
                })
            }
        
        # Return the first matching item
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(items[0], default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Failed to retrieve item: {str(e)}'})
        }