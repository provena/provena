### Record Creator Organisation
-   **_Record Creator Organisation\*_**: The organisation which is registering the data. This is searchable by typing the organisation's name in the search bar or manually entering the known ID of the Organisation.

### Dataset Approvals

{% include warning.html content="The Dataset Approvals section must be carefully considered by the registrant of the data. If you believe the dataset is subject to any of the below concerns, but the necessary consents, approvals or permissions have not been granted and/or provided, the dataset <b>should not be registered</b> in Provena's Data Store. Feel free to contact us if you are uncertain about registering a dataset." %}

-   **_Dataset Registration Ethics and Privacy\*_**: Does this dataset include any human data or require ethics/privacy approval for its **registration**? If so, have you included any required ethics approvals, consent from the participants and/or appropriate permissions to register this dataset in this information system? Required consents or permissions can be reposited as part of the dataset files where appropriate.
    -   **_Subject to ethics and privacy concerns for registration?_**: Use the tick box to specify whether this dataset is subject to ethical and privacy concerns for registration.
    -   **_Necessary consents and permissions required?_**: This tick box will only appear if the dataset is subject to the aforementioned concerns. If you have not acquired the necessary consents and permissions, the dataset should not be registered and submission will fail.
-   **_Dataset Access Ethics and Privacy\*_**: Does this dataset include any human data or require ethics/privacy approval for **enabling its access by users of the information system**? If so, have you included any required consent from the participants and/or appropriate permissions to facilitate access to this dataset in this information system? Required consents or permissions can be reposited as part of the dataset files where appropriate.
    -   **_Subject to ethics and privacy concerns for data access?_**: Use the tick box to specify whether this dataset is subject to ethical and privacy concerns for data access.
    -   **_Necessary consents and permissions required?_**: This tick box will only appear if the dataset is subject to the aforementioned concerns. If you have not acquired the necessary consents and permissions, the dataset should not be registered and submission will fail.
-   **_Indigenous Knowledge and Consent\*_**: Does this dataset contain Indigenous knowledge? If so, do you have consent from the relevant Indigenous communities for its use and access via this data store?
    -   **_Contains Indigenous knowledge?_**: Use the tick box to specify whether this dataset contains Indigenous knowledge.
    -   **_Necessary permission acquired?_**: This tick box will only appear if the dataset contains Indigenous knowledge. If you have not acquired the necessary consents and permissions, the dataset should not be registered and submission will fail.
-   **_Export Controls\*_**: Is this dataset subject to any export controls permits? If so, has this dataset cleared any required due diligence checks and have you obtained any required permits?
    -   **_Subject to export controls?_**: Use the tick box to specify whether this dataset is subject to export controls.
    -   **_Cleared due diligence checks and obtained required permits?_**: This tick box will only appear if the dataset was marked as subject to export controls. If you have not performed the necessary due diligence checks and acquired the relevant permits, the dataset should not be registered and submission will fail.

### Dataset Information

-   **_Dataset name\*_**: A title to identify the dataset well enough to disambiguate it from other datasets. i.e. "Coral reef locations with turtle activity in the Capricorn Group (Great Barrier Reef)"
-   **_Dataset description\*_**: Short description of the dataset. This should include the nature of the data, the intended usage, and any other relevant information.
    i.e. _The dataset Coral reef locations in the Capricorn Group (Great Barrier Reef), contains polygons of 150 reefs and islands that have turtle activity. The data was collected from satellite and survey information. Please see the readme.txt file for details on data processing steps undertaken. The data was obtained as part of the Reef Turtle monitoring program._
-   **_Access Info\*_**: Provides information about whether the dataset files will be stored in the Data Store, or hosted externally. Externally hosted datasets can be described and registered to enable data and activity provenance without enabling file upload or download. Use the checkbox “Store data in the Provena Data Store” to toggle this setting (checked indicates that the dataset is to be stored on the Provena Data Store, unchecked indicates that the dataset is stored externally). If the data is externally hosted, you must provide two additional fields:
    -   **_URI_**: Provide a valid [RFC3986](https://www.rfc-editor.org/rfc/rfc3986) URI which describes the location of the data. You should provide information about how to use this URI to access the data in the description below. Examples of valid URIs include: `http://website.com/file/path`, `https://website.com/file/path`, `ftp://ftp.server.com/file/path`,`file:///path/to/file`.
    -   **_Description_**: Provide a description of how the above URI can be used to access the dataset files.
-   **_Publisher\*_**: The organisation which is publishing/produced the data. This is searchable by typing the organisation's name in the search bar.
-   **_Dataset creation date\*_**: The date on which this version of the dataset was produced or generated.
-   **_Dataset publish date\*_**: The date on which this version of the dataset was first published. If the data has never been published before, please select today's date.
-   **_Usage licence\*_**: Select a licence from the dropdown list. The default will be 'Copyright'. A list of licences is available [here](../licenses.html){:target="\_blank"}.
-   **_Preferred Citation_**: Optionally specify a citation which users of this dataset should use when referencing this dataset. To provide a preferred citation, tick the "Provide preferred citation" checkbox and enter your citation into the textfield.
-   **_Keywords_**: List of keywords which describe the dataset. These keywords are searchable.

**_\*_** Denotes required field.
