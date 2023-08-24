## ECS SQS Job Async workflow Lambda Invoker

### Purpose

When a job is launched, an SNS topic fans out to multiple subs.

This lambda is invoked on the topic fan out.

It's job is to spin up an ECS task corresponding to the appropriate job type,
where there isn't already a suitable number of tasks running.

### Methodology

1. decode payloads from SNS topic message
2. parse the contents from payload (just as SNS level, not including specialised payload parsing)
3. determine which job type are present
4. find any public subnet within the VPC
5. conditionally launch task into the subnet for specified task definition (determined by task type)

**Note**: Currently, if any ECS task with the same task dfn is already running (or any non idle state), the lambda invoker will do nothing.

TODO investigate scaling past one container when queue is busy.
