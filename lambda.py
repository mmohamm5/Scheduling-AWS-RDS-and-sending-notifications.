import boto3
def lambda_handler(event, context):
  rds = boto3.client('rds')
  action = event['action']
  db_name = event['db_name']
  if action == 'start':
    response = rds.start_db_instance(DBInstanceIdentifier=db_name)
  else:
    response = rds.stop_db_instance(DBInstanceIdentifier=db_name)
print(f"{action} RDS Instance {db_name}: {response}")
return
