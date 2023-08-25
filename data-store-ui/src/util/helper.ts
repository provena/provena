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
