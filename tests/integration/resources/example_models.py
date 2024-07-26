<<<<<<< HEAD
from ProvenaInterfaces.RegistryModels import CollectionFormat, CollectionFormatAssociations, CollectionFormatApprovals, CollectionFormatDatasetInfo, OptionallyRequiredCheck, AccessInfo
=======
from ProvenaInterfaces.RegistryModels import *
>>>>>>> main

valid_collection_format1 = CollectionFormat(
    associations=CollectionFormatAssociations(
        organisation_id="1234"
    ),
    approvals=CollectionFormatApprovals(
        ethics_registration=OptionallyRequiredCheck(),
        ethics_access=OptionallyRequiredCheck(),
        export_controls=OptionallyRequiredCheck(),
        indigenous_knowledge=OptionallyRequiredCheck(),
    ),
    dataset_info=CollectionFormatDatasetInfo(
        name="Coral results 2021-02-30",
        description="Results of counterfactual model run",
        access_info=AccessInfo(
            reposited=True
        ),
        publisher_id="1234",
        created_date=CreatedDate(
            relevant=True,
            value="2021-12-25",
        ),
        published_date=PublishedDate(
            relevant=True,
            value="2021-12-25",
        ),
        license="https://creativecommons.org/licenses/by/4.0/",
        keywords=["keyword1", "keyword2"]
    )
)

valid_collection_format2 = CollectionFormat(
    associations=CollectionFormatAssociations(
        organisation_id="1234"
    ),
    approvals=CollectionFormatApprovals(
        ethics_registration=OptionallyRequiredCheck(),
        ethics_access=OptionallyRequiredCheck(),
        export_controls=OptionallyRequiredCheck(),
        indigenous_knowledge=OptionallyRequiredCheck(),
    ),
    dataset_info=CollectionFormatDatasetInfo(
        name="Coral results 2021-02-30",
        description="Results of counterfactual model run",
        access_info=AccessInfo(
            reposited=False,
            description="Fake",
            uri="https://fake.url.com"
        ),
        publisher_id="1234",
        created_date=CreatedDate(
            relevant=True,
            value="2021-12-25",
        ),
        published_date=PublishedDate(
            relevant=True,
            value="2021-12-25",
        ),
        license="https://creativecommons.org/licenses/by/4.0/",
        keywords=["keyword1", "keyword2"]
    )
)

valid_collection_format3 = CollectionFormat(
    associations=CollectionFormatAssociations(
        organisation_id="1234"
    ),
    approvals=CollectionFormatApprovals(
        ethics_registration=OptionallyRequiredCheck(),
        ethics_access=OptionallyRequiredCheck(),
        export_controls=OptionallyRequiredCheck(),
        indigenous_knowledge=OptionallyRequiredCheck(),
    ),
    dataset_info=CollectionFormatDatasetInfo(
        name="Coral results 2021-02-30",
        description="Results of counterfactual model run",
        access_info=AccessInfo(
            reposited=False,
            description="Fake",
            uri="https://fake.url.com"
        ),
        publisher_id="1234",
        created_date=CreatedDate(
            relevant=True,
            value="2021-12-25",
        ),
        published_date=PublishedDate(
            relevant=True,
            value="2021-12-25",
        ),
        license="https://creativecommons.org/licenses/by/4.0/",
        keywords=["keyword1", "keyword2", "coralLover"]
    )
)
