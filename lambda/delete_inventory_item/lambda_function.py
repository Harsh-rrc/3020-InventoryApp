import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Inventory')

def lambda_handler(event, context):
    try:
        print("Full event received:", json.dumps(event, indent=2))
        
        # Handle Lambda console testing vs real API Gateway calls
        item_id = None
        
        # If this is a Lambda console test with default event
        if event.get('key1') == 'value1' and event.get('key2') == 'value2':
            print("Lambda console test detected - using sample item ID")
            # Use a sample item ID that exists in your DynamoDB table
            item_id = "01JQ98X7P8A9R0P7L4N9X3WBQK"
        
        # If this is from API Gateway with Proxy Integration
        elif event.get('pathParameters') and event['pathParameters'].get('id'):
            item_id = event['pathParameters']['id']
            print(f"API Gateway call with ID: {item_id}")
        
        # If this is from API Gateway without Proxy Integration (mapping template)
        elif event.get('id'):
            item_id = event.get('id')
            print(f"API Gateway call with ID: {item_id}")
        
        if not item_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Item ID is required',
                    'usage': 'Send DELETE request to: /item/YOUR-ITEM-ID',
                    'example_item_id': '01JQ98X7P5X6O7M4I1K6U0TYNH'
                })
            }
        
        print(f"DELETING item: {item_id}")
        
        # First, query to find the item and get its location_id
        response = table.query(
            KeyConditionExpression=Key('item_id').eq(item_id)
        )
        
        items = response.get('Items', [])
        
        if not items:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Item not found in database',
                    'item_id': item_id,
                    'suggestion': 'Check that the item exists in DynamoDB'
                })
            }
        
        # Get the location_id from the found item
        location_id = items[0]['location_id']
        item_name = items[0]['item_name']
        
        # Convert Decimal to int/float for JSON serialization
        if isinstance(location_id, Decimal):
            location_id = int(location_id)
        
        # ACTUALLY DELETE THE ITEM from DynamoDB
        table.delete_item(
            Key={
                'item_id': item_id,
                'location_id': location_id
            }
        )
        
        print(f"SUCCESS: Deleted {item_name} (ID: {item_id}) from location {location_id}")
        
        # SUCCESS RESPONSE - Convert all values to JSON-serializable types
        response_data = {
            'message': 'Item successfully deleted from database',
            'deleted_item_id': item_id,
            'deleted_item_name': item_name,
            'deleted_from_location': location_id
        }
        
        # Custom JSON encoder to handle Decimal objects
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return int(obj) if obj % 1 == 0 else float(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data, default=decimal_default)
        }
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Failed to delete item: {str(e)}'})
        }