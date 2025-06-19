from aws_cdk import (
    aws_backup as backup,
    RemovalPolicy,
    Duration,
    aws_events as events,
    aws_iam as iam,
    Annotations,
    aws_kms as kms
)

from constructs import Construct
from typing import Any, Optional, List, cast
from aws_cron_expression_validator.validator import AWSCronExpressionValidator  # type: ignore


class BackupService(Construct):
    def __init__(self,
                 scope: Construct,
                 id: str,
                 vault_name: Optional[str] = None,
                 alias_name: Optional[str] = None,
                 existing_vault_arn: Optional[str] = None,
                 critical_plan_name: Optional[str] = None,
                 non_critical_plan_name: Optional[str] = None,
                 data_storage_plan_name: Optional[str] = None,
                 trusted_copy_source_account_ids: Optional[List[str]] = None,
                 trusted_copy_destination_account_ids: Optional[List[str]] = None,
                 existing_vault_key: Optional[kms.IKey] = None,
                 key_admins: List[iam.IPrincipal] = [],
                 **kwargs: Any) -> None:
        """Creates a backup vault, plans and rules to enable 
        automated backup of "critical" and "non critical" resources.

        If you already have a vault setup, you can specify it using the 
        existing vault arn. It will be soft imported (i.e. referenced). 

        You can also specify the vault name to override the auto generated 
        name.

        Parameters
        ----------
        scope : Construct
            The CDK scope
        id : str
            The construct id
        vault_name : Optional[str], optional
            The name of the vault, by default None
        existing_vault_arn : Optional[str], optional
            The ARN of an existing vault to use instead 
            of producing a new one in this stack, by default None
        """
        super().__init__(scope, id, **kwargs)

        # setup a backup vault - either using existing
        # or creating one from scratch
        # see existing_vault_arn above
        if existing_vault_arn:
            vault = backup.BackupVault.from_backup_vault_arn(
                scope=self,
                id='vault',
                backup_vault_arn=existing_vault_arn
            )
            if existing_vault_key is not None or len(key_admins) > 0:
                Annotations.of(self).add_warning(
                    "Cannot explicitly associated provided KMS key with existing vault.")

            if trusted_copy_source_account_ids:
                if len(trusted_copy_source_account_ids) > 0:
                    Annotations.of(self).add_warning(
                        "Cannot append trusted accounts to access policy of imported from ARN backup vault!")

            if trusted_copy_destination_account_ids:
                if len(trusted_copy_destination_account_ids) > 0:
                    Annotations.of(self).add_warning(
                        "Cannot append trusted accounts for kms copy destinations for imported from ARN backup vault!")

        else:
            # Create an encryption key for the vault if no existing key was
            # provided - this enables cross account copying
            self.vault_kms_key: kms.IKey
            if existing_vault_key is None:
                # Create new key
                self.vault_kms_key = cast(kms.IKey, kms.Key(
                    scope=self,
                    id='key',
                    description=f'Encryption key for Provena backup vault, {vault_name=}.',
                    enabled=True,
                    enable_key_rotation=True,
                    admins=key_admins,
                ))

                # add a kms key alias if either the alias name or vault name is provided
                if alias_name:
                    self.vault_kms_key.add_alias(alias_name)
                elif vault_name:
                    self.vault_kms_key.add_alias(f"{vault_name}_key")

                if trusted_copy_destination_account_ids:
                    for account_id in trusted_copy_destination_account_ids:
                        # Allow the trusted destination account to decrypt using this key
                        # It also needs to be able to describe it
                        # TODO validate minimum viable set of permissions
                        self.vault_kms_key.grant(
                            iam.AccountPrincipal(account_id),
                            "kms:Describe*",
                            "kms:Decrypt"
                        )
            else:
                # Reference existing key
                self.vault_kms_key = existing_vault_key

                if trusted_copy_destination_account_ids:
                    if len(trusted_copy_destination_account_ids) > 0:
                        Annotations.of(self).add_warning(
                            "Cannot update access policy of imported KMS key!")

            # use the created key
            if vault_name:
                vault = backup.BackupVault(
                    scope=self,
                    id='vault',
                    backup_vault_name=vault_name,
                    removal_policy=RemovalPolicy.RETAIN,
                    encryption_key=self.vault_kms_key
                )
            else:
                vault = backup.BackupVault(
                    scope=self,
                    id='vault',
                    removal_policy=RemovalPolicy.RETAIN,
                    encryption_key=self.vault_kms_key
                )

            # Add vault permissions for copies if provided
            if trusted_copy_source_account_ids:
                for account_id in trusted_copy_source_account_ids:
                    # Enable copy from trusted account into account_id
                    vault.add_to_access_policy(
                        iam.PolicyStatement(
                            actions=["backup:CopyIntoBackupVault"],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                            principals=[
                                cast(iam.IPrincipal, iam.AccountPrincipal(
                                    account_id=account_id))
                            ]
                        )
                    )

        # setup backup plan(s)

        # this is the plan to be used for critical resources

        # use the name specified if provided or a default
        plan_name = critical_plan_name if critical_plan_name else 'critical-backup-plan'

        critical_plan = backup.BackupPlan(
            scope=self,
            id='critical-backup-plan',
            backup_plan_name=plan_name,
            backup_vault=vault
        )

        # critical plan takes daily snapshots which:
        # moves to cold storage after 30 days
        # are retained for 3 months
        daily_midnight_cron = "0 0 * * ? *"
        # check validity of cron before trying to deploy
        AWSCronExpressionValidator.validate(daily_midnight_cron)
        critical_plan.add_rule(
            rule=backup.BackupPlanRule(
                # use the plan backup vault
                # backup_vault = ...

                # move to cold storage? (1 month)
                move_to_cold_storage_after=Duration.days(30),

                # continuous backup not enabled right now
                # enable_continuous_backup ...

                # retain the snapshot for 4 months ( must be 3 months greater than cold storage)
                delete_after=Duration.days(120),

                # how often to take the snapshot?
                # cron expression - daily
                schedule_expression=events.Schedule.expression(
                    f"cron({daily_midnight_cron})"),
            )
        )

        # this is the plan to be used for non-critical resources

        # use the name specified if provided or a default
        plan_name = non_critical_plan_name if non_critical_plan_name else 'non-critical-backup-plan'

        non_critical_plan = backup.BackupPlan(
            scope=self,
            id='non-critical-backup-plan',
            backup_plan_name=plan_name,
            backup_vault=vault
        )

        # non critical plan takes weekly snapshots which:
        # moves to cold storage after 7 days
        # are retained for 1 month
        weekly_sunday_cron = "0 2 ? * SUN *"
        # check validity of cron before trying to deploy
        AWSCronExpressionValidator.validate(weekly_sunday_cron)

        non_critical_plan.add_rule(
            rule=backup.BackupPlanRule(
                # use the plan backup vault
                # backup_vault = ...

                # retain the snapshot for 1 month - no cold storage
                delete_after=Duration.days(30),

                # how often to take the snapshot?
                # this is aws events schedule expression - weekly 2am on Sunday
                schedule_expression=events.Schedule.expression(
                    f"cron({weekly_sunday_cron})")
            )
        )

        # this is the plan to be used for large storage layers e.g. s3 buckets

        # use the name specified if provided or a default
        plan_name = data_storage_plan_name if data_storage_plan_name else 'data-storage-backup-plan'

        data_storage_plan = backup.BackupPlan(
            scope=self,
            id='data-storage-backup-plan',
            backup_plan_name=plan_name,
            backup_vault=vault
        )

        # the S3 data storage plan in general should have a high resolution for
        # short window recoveries while avoiding data duplication as much as
        # possible. Combination of short time span high resolution recovery and
        # longer term backups.

        # rule 1 - hourly virtual snapshots of continuous PITR. Retain PITR up
        # to maximum of 35 days. This incurs one snapshot (duplicate) +
        # transaction logs.

        hourly_cron = "0 * * * ? *"
        # check validity of cron before trying to deploy
        AWSCronExpressionValidator.validate(hourly_cron)

        data_storage_plan.add_rule(
            rule=backup.BackupPlanRule(
                # for S3 we want PITR enabled
                enable_continuous_backup=True,

                # S3 doesn't support cold storage so no need to specify

                # retain snapshots for a week + some buffer
                delete_after=Duration.days(35),

                # snapshots are incremental for supported resources - don't use
                # this plan for dynamoDB, documentDB or other non supported
                # incremental resources - these are just helpful restore points
                # - set to hourly so we can quick spin back to hourly PIT
                schedule_expression=events.Schedule.expression(
                    f"cron({hourly_cron})")
            )
        )

        # rule 2 - less frequent longer retained backups - currently monthly
        # backup retained for 90 days (i.e. overlap to enable buffer in case of
        # backup failure) - don't use for non incremental large data stores

        monthly_cron = "0 2 1 * ? *"
        # check validity of cron before trying to deploy
        AWSCronExpressionValidator.validate(monthly_cron)
        data_storage_plan.add_rule(
            rule=backup.BackupPlanRule(
                # retain snapshots for a little over a month
                # maximum of two overlapped snapshots
                delete_after=Duration.days(90),

                # Monthly snapshot at 2am first day of every month
                schedule_expression=events.Schedule.expression(
                    f"cron({monthly_cron})")
            )
        )

        # expose for construct interface
        self.vault = vault
        self.critical_plan = critical_plan
        self.non_critical_plan = non_critical_plan
        self.data_storage_plan = data_storage_plan

    def register_critical_resource(self, id: str, resource: backup.BackupResource, allow_restores: bool = True) -> None:
        """Will add a resource (AWS Backup BackupResource) as a resource on all 
        critical backup plans.

        This should be 

        Parameters
        ----------
        id : str
            The construct id
        resource : backup.BackupResource
            The resource to add
        allow_restores : bool, optional
            Should the aws backup service be able to 
            restore the resource, by default True
        """
        # add the selection to the critical plan
        self.critical_plan.add_selection(
            id=id,
            resources=[resource],
            allow_restores=allow_restores
        )

    def register_non_critical_resource(self, id: str, resource: backup.BackupResource, allow_restores: bool = True) -> None:
        """Will add a resource (AWS Backup BackupResource) as a resource on all 
        non critical backup plans.

        Parameters
        ----------
        id : str
            The construct id
        resource : backup.BackupResource
            The resource to add
        allow_restores : bool, optional
            Should the aws backup service be able to 
            restore the resource, by default True
        """
        # add the selection to the critical plan
        self.non_critical_plan.add_selection(
            id=id,
            resources=[resource],
            allow_restores=allow_restores
        )

    def register_data_storage_resource(self, id: str, resource: backup.BackupResource, enable_s3_permissions: bool = False, allow_restores: bool = True) -> None:
        """
        Will add a resource (AWS Backup BackupResource) as a resource on data
        storage plans.

        Parameters
        ----------
        id : str
            The construct id
        resource : backup.BackupResource
            The resource to add
        allow_restores : bool, optional
            Should the aws backup service be able to restore the resource, by
            default True
        """
        # possibly setup a default iam role with the required permissions
        role: Optional[iam.IRole] = None
        if enable_s3_permissions:
            # Rebuild the basic role
            role = iam.Role(
                scope=self,
                id=id + 'ServiceRole',
                assumed_by=iam.ServicePrincipal('backup.amazonaws.com'))

            # Add backup permission
            role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSBackupServiceRolePolicyForBackup")
            )
            role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AWSBackupServiceRolePolicyForS3Backup")
            )

            # optionally add restore permission
            if allow_restores:
                role.add_managed_policy(
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "service-role/AWSBackupServiceRolePolicyForRestores")
                )
                role.add_managed_policy(
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "AWSBackupServiceRolePolicyForS3Restore")
                )

        # add the selection to the critical plan
        selection = self.data_storage_plan.add_selection(
            id=id,
            resources=[resource],
            allow_restores=allow_restores,
            # Either auto generated or s3 special role
            role=role
        )
