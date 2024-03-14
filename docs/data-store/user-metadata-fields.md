### Record Creator Organisation

- **_Record Creator Organisation\*_**: The [registered Organisation](../provenance/registering-model-runs/establishing-required-entities#organisation) which is registering the data. This is searchable by typing the Organisation's name in the search bar or manually entering the known ID of the Organisation.
- **_Dataset Custodian_**: The [registered Person](../provenance/registering-model-runs/establishing-required-entities#person) who could best be described as the custodian of this data. This is searchable by typing the Person's name in the search bar or manually entering the known ID of the Person.
- **_Point of Contact_**: Please provide a point of contact for enquiries about this data e.g. email address. Please ensure you have sought consent to include these details in the record.

### Dataset Approvals

{% include warning.html content="The Dataset Approvals section must be carefully considered by the registrant of the data. If you believe the dataset is subject to any of the below concerns, but the necessary consents, approvals or permissions have not been granted and/or provided, the dataset <b>should not be registered</b> in Provena's Data Store. Feel free to contact us if you are uncertain about registering a dataset." %}

- **_Dataset Registration Ethics and Privacy\*_**: Does this dataset include any human data or require ethics/privacy approval for its **registration**? If so, have you included any required ethics approvals, consent from the participants and/or appropriate permissions to register this dataset in this information system? Required consents or permissions can be reposited as part of the dataset files where appropriate.
  - **_Subject to ethics and privacy concerns for registration?_**: Use the tick box to specify whether this dataset is subject to ethical and privacy concerns for registration.
  - **_Necessary consents and permissions required?_**: This tick box will only appear if the dataset is subject to the aforementioned concerns. If you have not acquired the necessary consents and permissions, the dataset should not be registered and submission will fail.
- **_Dataset Access Ethics and Privacy\*_**: Does this dataset include any human data or require ethics/privacy approval for **enabling its access by users of the information system**? If so, have you included any required consent from the participants and/or appropriate permissions to facilitate access to this dataset in this information system? Required consents or permissions can be reposited as part of the dataset files where appropriate.
  - **_Subject to ethics and privacy concerns for data access?_**: Use the tick box to specify whether this dataset is subject to ethical and privacy concerns for data access.
  - **_Necessary consents and permissions required?_**: This tick box will only appear if the dataset is subject to the aforementioned concerns. If you have not acquired the necessary consents and permissions, the dataset should not be registered and submission will fail.
- **_Indigenous Knowledge and Consent\*_**: Does this dataset contain [Indigenous Knowledge](https://www.ipaustralia.gov.au/understanding-ip/indigenous-knowledge)? If so, do you have consent from the relevant Indigenous communities for its use and access via this data store?
  - **_Contains Indigenous Knowledge?_**: Use the tick box to specify whether this dataset contains Indigenous Knowledge.
  - **_Necessary permission acquired?_**: This tick box will only appear if the dataset contains Indigenous Knowledge. If you have not acquired the necessary consents and permissions, the dataset should not be registered and submission will fail.
- **_Export Controls\*_**: Is this dataset subject to any export controls permits? If so, has this dataset cleared any required due diligence checks and have you obtained any required permits?
  - **_Subject to export controls?_**: Use the tick box to specify whether this dataset is subject to export controls.
  - **_Cleared due diligence checks and obtained required permits?_**: This tick box will only appear if the dataset was marked as subject to export controls. If you have not performed the necessary due diligence checks and acquired the relevant permits, the dataset should not be registered and submission will fail.

### Dataset Information

- **_Dataset name\*_**: A title to identify the dataset well enough to disambiguate it from other datasets. i.e. "Coral reef locations with turtle activity in the Capricorn Group (Great Barrier Reef)"
- **_Dataset description\*_**: Short description of the dataset. This should include the nature of the data, the intended usage, and any other relevant information.
  i.e. _The dataset Coral reef locations in the Capricorn Group (Great Barrier Reef), contains polygons of 150 reefs and islands that have turtle activity. The data was collected from satellite and survey information. Please see the readme.txt file for details on data processing steps undertaken. The data was obtained as part of the Reef Turtle monitoring program._
- **_Access Info\*_**: Provides information about whether the dataset files will be stored in the Data Store, or hosted externally. [Externally hosted](./externally-hosted-datasets) datasets can be described and registered to enable data and activity provenance without enabling file upload or download. Use the checkbox “Store data in the Provena Data Store” to toggle this setting (checked indicates that the dataset is to be stored on the Provena Data Store, unchecked indicates that the dataset is stored externally). If the data is externally hosted, you must provide two additional fields:
  - **_URI_**: Provide a valid [RFC3986](https://www.rfc-editor.org/rfc/rfc3986) URI which describes the location of the data. You should provide information about how to use this URI to access the data in the description below. Examples of valid URIs include: `http://website.com/file/path`, `https://website.com/file/path`, `ftp://ftp.server.com/file/path`,`file:///path/to/file`.
  - **_Description_**: Provide a description of how the above URI can be used to access the dataset files.
- **_Publisher\*_**: The [registered Organisation](../provenance/registering-model-runs/establishing-required-entities#organisation) which is publishing/produced the data. This is searchable by typing the Organisation's name in the search bar.
- **_Dataset creation date\*_**: The date on which this version of the dataset was produced or generated.
- **_Dataset publish date\*_**: The date on which this version of the dataset was first published. If the data has never been published before, please select today's date.
- **_Usage licence\*_**: Select a licence from the dropdown list. The default will be 'Copyright'. A list of licences is available [here](../licenses.html){:target="\_blank"}.
- **_Dataset purpose_**: A brief description of the reason a data asset was created. Should be a good guide to the potential usefulness of a data asset to other users.
- **_Dataset rights holder_**: Specify the party owning or managing rights over the resource. Please ensure you have sought consent to include these details in the record.
- **_Usage limitations_**: A statement that provides information on any caveats or restrictions on access or on the use of the data asset, including legal, security, privacy, commercial or other limitations.
- **_Preferred Citation_**: Optionally specify a citation which users of this dataset should use when referencing this dataset. To provide a preferred citation, tick the "Provide preferred citation" checkbox and enter your citation into the textfield.
- **_Spatial Information_**: If your dataset includes spatial data, you can provide more information about the extent and resolution of this data.
  - **_Spatial Coverage_**: The geographic area applicable to the data asset. Please specify spatial coverage using the [EWKT](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) format.
  - **_Spatial Resolution_**: The spatial resolution applicable to the data asset. Please use the [Decimal Degrees](https://en.wikipedia.org/wiki/Decimal_degrees) standard.
  - **_Spatial Extent_**: The range of spatial coordinates applicable to the data asset. Please provide a bounding box extent using the [EWKT](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) format.
- **_Temporal Information_**: If your dataset includes data spanning a period of time, you can provide more information about the duration and resolution of this data.
  - **_Temporal Duration_**: The start and end date of the time period applicable to the data asset (note that a start and end date both must be provided if a temporal duration is to be specified).
  - **_Temporal Resolution_**: The temporal resolution (i.e. time step) of the data. Please use the [ISO8601 duration format](https://en.wikipedia.org/wiki/ISO_8601#Durations) e.g. "P1Y2M10DT2H30M".
- **_Dataset File Formats_**: What file formats are present in this dataset? E.g. "pdf", "csv" etc. You can use the plus and minus symbol to add and remove file formats.
- **_Keywords_**: List of keywords which describe the dataset. These keywords are searchable.
- **_Custom User Metadata_**: If you would like to include additional custom annotations to describe your dataset, you can do so here. Please tick "Include Custom User Metadata" and then click the "Add a new entry" plus icon to add a row. Your metadata is composed of a set of key value pairs. Click and enter a key, and value, for example "my_special_dataset_id" and "1234". You can add another row using the plus icon on the right, or remove an entry using the red minus sign on the right. To remove all custom metadata, untick the "Include Custom User Metadata" box.

**_\*_** Denotes required field.
