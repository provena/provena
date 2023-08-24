# Async Job ECS SQS Workflow Package

## Purpose

This package provides methods to help manage the tasks of an ECS job container in our async workflow.

## Classes/Methods

-   **DynamoTools** : contains helpers for interacting with the job status table
-   **JobRunner** : contains the main entry point for a running ECS task - this includes a polling and job callback dispatching workflow
-   **SqsTools** : contains helper functions for interacting with the SQS queue - includes dequeueing and fininshing work by reporting back
-   **Types** : some shared types to help with static typing
-   **Workflow** : some primary workflow methods such as polling for work, reporting status etc.
-   **Settings** : set of required env variables for running an ECS job service

## Recommended usage

Ensure the consuming task has the required env variables from the Settings class.

In the ECS task, call the JobRunner.ecs_job_worker with the desired callback.

This will handle dispatching tasks to the callback.

**NOTE**: This dispatches at the `JobType` level - sub type dispatching is handled by the ECS container.
