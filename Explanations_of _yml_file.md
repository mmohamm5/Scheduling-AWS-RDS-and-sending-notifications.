The template automates the **start** and **stop** scheduling of an **AWS RDS (PostgreSQL)** instance using **Lambda**, **EventBridge**, and **SNS** for notifications.

---

### **Template Header**  
```yaml
AWSTemplateFormatVersion: "2010-09-09"
```
- **AWSTemplateFormatVersion:** Specifies the version of the CloudFormation template language. `"2010-09-09"` is the latest and most common version.

```yaml
Description: Resources for automatic stop and start of instances during non working hours.
```
- **Description:** A short description of what the template does — in this case, scheduling RDS start/stop during off-hours.

---

### **Resources Section**  
The `Resources` block defines all the AWS components this template will create.

---

### **1. SNS Topic for RDS Notifications**  
```yaml
ScheduledRestartTopic:
  Type: AWS::SNS::Topic
  Properties:
    TopicName: ScheduledRestartTopic
```
- **ScheduledRestartTopic:** Logical name for the SNS topic (used for referencing within the template).  
- **Type:** Specifies the AWS resource type. Here, it's an **SNS Topic** (`AWS::SNS::Topic`).  
- **Properties > TopicName:** The name given to the SNS topic. This topic will send notifications about RDS events (like start, stop, or failure).

---

### **2. RDS Event Subscription**  
```yaml
DevRDSEventSubscription:
  Type: AWS::RDS::EventSubscription
  Properties:
    SnsTopicArn: !Ref ScheduledRestartTopic
```
- **DevRDSEventSubscription:** Logical name for the RDS event subscription.  
- **Type:** Specifies it’s an **RDS event subscription** (`AWS::RDS::EventSubscription`).  
- **SnsTopicArn:** Links the SNS topic we just created using `!Ref` (reference to `ScheduledRestartTopic`).

```yaml
    SourceType: "db-instance"
```
- **SourceType:** Indicates we’re subscribing to events from a **database instance**.

```yaml
    EventCategories:
      - "availability"
      - "configuration change"
      - "notification"
      - "failure"
```
- **EventCategories:** Lists the RDS event types that will trigger notifications (e.g., availability issues, config changes, etc.).

```yaml
    SourceIds:
      - "test-db-shawon"
```
- **SourceIds:** The **identifier** of the RDS instance this subscription applies to (`test-db-shawon`).

```yaml
    Enabled: true
```
- **Enabled:** The event subscription is **active** (`true`).

---

### **3. IAM Role for Lambda Execution**  
IAM roles grant permissions to the Lambda function.

```yaml
LambdaExecutionRole:
  Type: AWS::IAM::Role
  Properties:
    RoleName: ScheduledRestartExecutionRole
```
- **LambdaExecutionRole:** Logical name for the IAM role.  
- **Type:** IAM Role (`AWS::IAM::Role`).  
- **RoleName:** The role's name in AWS.

```yaml
    AssumeRolePolicyDocument:
      Version: "2012-10-17"
```
- **AssumeRolePolicyDocument:** Defines **who can assume this role**.  
- **Version:** Policy language version.

```yaml
      Statement:
        - Effect: Allow
          Principal:
            Service: lambda.amazonaws.com
          Action: sts:AssumeRole
```
- **Statement:**  
  - **Effect:** Allows the action.  
  - **Principal:** Specifies **Lambda service** as the entity that can assume this role.  
  - **Action:** `sts:AssumeRole` allows Lambda to use this role.

---

#### **IAM Role Policies**  
```yaml
    Policies:
      - PolicyName: ScheduledRestartPolicy
        PolicyDocument:
          Version: "2012-10-17"
          Statement:
```
- **Policies:** Inline IAM policy attached to the role.  
- **PolicyName:** The name of the policy.  
- **PolicyDocument:** Defines the permissions.

```yaml
            # Logs permissions
            - Effect: Allow
              Action:
                - logs:CreateLogGroup
                - logs:CreateLogStream
                - logs:PutLogEvents
              Resource: "arn:aws:logs:*:*:*"
```
- **Logs permissions:** Grants Lambda permission to write logs to **CloudWatch**.

```yaml
            # Start and Stop RDS instance permissions
            - Effect: Allow
              Action:
                - rds:StartDBInstance
                - rds:StopDBInstance
              Resource: "arn:aws:rds:us-east-1:109707880541:db:test-db-shawon"
```
- **RDS permissions:** Allows Lambda to **start** and **stop** the specified RDS instance.

---

### **4. Lambda Function for RDS Scheduling**  
```yaml
LambdaFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: ScheduledRestartFunction
    Runtime: python3.13
    Handler: index.lambda_handler
```
- **LambdaFunction:** Logical name for the Lambda function.  
- **Type:** Specifies this is a Lambda function.  
- **FunctionName:** Name of the Lambda function in AWS.  
- **Runtime:** The Python version (`python3.13`).  
- **Handler:** Specifies the entry point (`index.lambda_handler`).

```yaml
    Role: !GetAtt LambdaExecutionRole.Arn
```
- **Role:** Grants the Lambda function the **IAM role** created earlier (`LambdaExecutionRole`).

---

#### **Lambda Inline Python Code**  
```yaml
    Code:
      ZipFile: |
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
```
- **ZipFile:** Inline Python code for the Lambda function.  
- **Code Logic:**  
  - Uses `boto3` (AWS SDK for Python) to interact with RDS.  
  - Checks if the action is **start** or **stop** based on the incoming event.  
  - Executes `start_db_instance()` or `stop_db_instance()` accordingly.  
  - Logs the response.

---

### **5. EventBridge Rule - Start RDS at 7:00 AM (UTC)**  
```yaml
EventBridgeRuleStart:
  Type: AWS::Events::Rule
  Properties:
    Name: DevRDSStartRule
    ScheduleExpression: "cron(0 6 ? * MON-FRI *)"
```
- **EventBridgeRuleStart:** Logical name for the **EventBridge rule**.  
- **Type:** Specifies an EventBridge rule.  
- **ScheduleExpression:** The **cron expression** here (`0 6 ? * MON-FRI *`) means:  
  - **6 AM UTC** (likely 7 AM local if UTC+1)  
  - **Monday–Friday** only.

```yaml
    State: ENABLED
    Targets:
      - Arn: !GetAtt LambdaFunction.Arn
        Id: DevRDSStartAction
        Input: '{"action": "start", "db_name": "test-db-shawon"}'
```
- **State:** Enables the rule immediately.  
- **Targets:** Specifies the **Lambda function** that should run on the schedule, passing the action `"start"`.

---

### **6. EventBridge Rule - Stop RDS at 9:00 PM (UTC)**  
```yaml
EventBridgeRuleStop:
  Type: AWS::Events::Rule
  Properties:
    Name: DevStopRule
    ScheduleExpression: "cron(0 20 ? * MON-FRI *)"
```
- Same as the **start rule**, but this triggers at **9 PM UTC** to **stop** the RDS instance.

```yaml
    Targets:
      - Arn: !GetAtt LambdaFunction.Arn
        Id: DevRDSStopAction
        Input: '{"action": "stop", "db_name": "test-db-shawon"}'
```
- The **Input** here specifies `"action": "stop"`.

---

### **7. Lambda Permission for EventBridge**  
```yaml
LambdaPermissionForEventBridge:
  Type: AWS::Lambda::Permission
  Properties:
    FunctionName: !Ref LambdaFunction
    Action: "lambda:InvokeFunction"
    Principal: "events.amazonaws.com"
```
- **LambdaPermissionForEventBridge:** Grants **EventBridge** permission to invoke the Lambda function.  
- **FunctionName:** References the Lambda function.  
- **Action:** Specifies the action permitted (`lambda:InvokeFunction`).  
- **Principal:** Identifies **EventBridge** (`events.amazonaws.com`) as the AWS service allowed to invoke Lambda.

---

###  **Summary of Workflow**  
1. **SNS Topic:** Sends notifications for RDS instance events.  
2. **RDS Event Subscription:** Monitors specific events for the RDS instance.  
3. **IAM Role:** Grants Lambda permission to manage RDS and write logs.  
4. **Lambda Function:** Python code that starts or stops the RDS instance based on the triggered event.  
5. **EventBridge Rules:**  
   - **Start RDS at 7 AM** (UTC) Monday–Friday.  
   - **Stop RDS at 9 PM** (UTC) Monday–Friday.  
6. **Permissions:** EventBridge can invoke the Lambda function.

---

Let me know if you want deeper explanations on any AWS service used or the Python logic in the Lambda function! 🚀
