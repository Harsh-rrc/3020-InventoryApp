import json
import boto3
import uuid
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Inventory')

def lambda_handler(event, context):
    try:
        print("Full event received:", json.dumps(event, indent=2))
        
        # Handle both API Gateway calls and Lambda console testing
        body = {}
        
        # If this is from API Gateway (with body)
        if 'body' in event and event['body']:
            body = json.loads(event['body'])
            print("Processing API Gateway request")
        # If this is direct Lambda console test (data in event root)
        else:
            body = event
            print("Processing Lambda console test")
        
        # Validate required fields
        required_fields = ['item_name', 'item_description', 'item_qty_on_hand', 'item_price', 'location_id']
        for field in required_fields:
            if field not in body:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': f'Missing required field: {field}',
                        'required_fields': required_fields
                    })
                }
        
        # Generate a unique ID using UUID
        item_id = str(uuid.uuid4())
        
        # Prepare the item for DynamoDB - USE DECIMAL for numbers
        new_item = {
            'item_id': item_id,
            'item_name': body['item_name'],
            'item_description': body['item_description'],
            'item_qty_on_hand': int(body['item_qty_on_hand']),  # int is fine for whole numbers
            'item_price': Decimal(str(body['item_price'])),     # Use Decimal for prices
            'location_id': int(body['location_id'])             # int is fine for location
        }
        
        # Put the item in DynamoDB
        table.put_item(Item=new_item)
        
        print(f"SUCCESS: Added item {body['item_name']} with ID: {item_id}")
        
        # Custom JSON encoder to handle Decimal objects
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj)  # Convert Decimal to float for JSON response
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        # SUCCESS RESPONSE
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Item added successfully',
                'item_id': item_id,
                'item': new_item
            }, default=decimal_default)
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Failed to add item: {str(e)}'})
        }