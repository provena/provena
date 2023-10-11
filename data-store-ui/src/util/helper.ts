export const datasetVersionIdLinkResolver = (id: string): string => {
    // Help versioning items redirect to their tabs
    return `/dataset/${id}?view=versioning`;
};

export const datasetApprovalsTabLinkResolver = (id: string): string => {
    // redirect to dataset approvals tab
    return `/dataset/${id}?view=approvals`;
};

export const datasetApprovalTakeActionLinkResolver = (id: string): string => {
    // Generate the link for approval requests list take action button,
    // redirect to dataset approvals take action page
    return `/approval-action/${id}`;
};

export const copyToClipboard = (content: string) => {
    navigator.clipboard.writeText(content);
};

export const initiateDownload = (url: string, filename: string) => {
    // Note that this relies on the content disposition of the URL server
    // response preferring attachment - otherwise it will open a preview

    // Generate the download element
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;

    // Initiate download
    link.click();

    // Clean up by removing the link element
    document.body.removeChild(link);
};
