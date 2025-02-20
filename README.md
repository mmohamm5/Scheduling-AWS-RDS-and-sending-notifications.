# Scheduling-AWS-RDS-and-sending-notifications.
```bash
aws cloudformation deploy --stack-name FullRDSSetup --template-file shawon.yaml --capabilities CAPABILITY_NAMED_IAM
```
## Work flow ##
** Create RDS in AWS **
1. Go to the RDS page and choose Standard create > PostgreSQL
2. Engine version > choose latest one.
3. Templates > Free tier. ( for test case)
4. DB instance identifier > give a unique name. this identifier will use in cloud formation template.
5. Master user name > use a user name & Master password > choose a password. (Remember this user name and password)
6. Public acess > I choosed Yes . (Normally DB should not be public)
7. Additional configuration > initial database name > give a name.
8. Now create database.

![RDS created](asset/db1.JPG)



