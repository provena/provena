import { useState } from "react";
import { ItemDataset } from "../shared-interfaces/DataStoreAPI";

// Helper functions

const getOrganisation = (dataset: ItemDataset): string => {
    return dataset.collection_format.dataset_info.publisher_id;
};

const organisationFilter = (dataset: ItemDataset, org: string): boolean => {
    return getOrganisation(dataset) === org;
};

const deriveOrganisationListCount = (datasets: ItemDataset[]) => {
    const orgs: Map<string, number> = new Map([]);

    for (const ds of datasets) {
        const org = getOrganisation(ds);
        const currentCount = orgs.get(org) ?? 0;
        orgs.set(org, currentCount + 1);
    }

    // Sort alphabetically and return counts
    return { organisationList: Array.from(orgs.keys()).sort(), counts: orgs };
};

interface useOrganisationFilterProps {
    datasets: ItemDataset[];
}
interface useOrganisationFilterResponse {
    organisations: string[];
    organisationCounts: Map<string, number>;
    selectedOrganisations: string[];
    selectOrganisation: (org: string) => void;
    deselectOrganisation: (org: string) => void;
    clearOrganisations: () => void;
    filteredDatasets: ItemDataset[];
    filteredCount: number;
}
export const useOrganisationFilter = (
    props: useOrganisationFilterProps
): useOrganisationFilterResponse => {
    /**
    Hook: useOrganisationFilter

    Provided a list of input datasets gives controls to filter the list based on
    selected organisations. Also provides a list of valid organisations and
    their counts.
    */

    // Get the org list and count
    const { organisationList, counts } = deriveOrganisationListCount(
        props.datasets
    );

    // Maintain a list of selected organisations
    const [selectedOrganisations, setSelectedOrganisations] = useState<
        string[]
    >([]);

    // Handlers to interact with org list
    const addOrganisation = (org: string) => {
        if (organisationList.indexOf(org) === -1) {
            console.log("Invalid organisation: " + org);
        } else {
            const copy: string[] = JSON.parse(
                JSON.stringify(selectedOrganisations)
            );
            copy.push(org);
            setSelectedOrganisations(copy);
        }
    };

    const removeOrganisation = (org: string) => {
        const copy: string[] = JSON.parse(
            JSON.stringify(selectedOrganisations)
        );
        const index = copy.indexOf(org);
        if (index !== -1) {
            // Remove that element
            copy.splice(index, 1);
        }
        setSelectedOrganisations(copy);
    };

    const clearOrganisations = () => {
        setSelectedOrganisations([]);
    };

    // Filter the input dataset list based on selected organisations
    // We make a copy here so we don't mutate the list
    var filteredDatasetList: ItemDataset[] = [];

    // Selection made - only include datasets in the filtered list if filter matches
    if (selectedOrganisations.length > 0) {
        for (const dataset of props.datasets) {
            var include = false;
            for (const org of selectedOrganisations) {
                if (organisationFilter(dataset, org)) {
                    include = true;
                    break;
                }
            }
            if (include) {
                filteredDatasetList.push(JSON.parse(JSON.stringify(dataset)));
            }
        }
    } else {
        // include all the datasets
        filteredDatasetList = JSON.parse(JSON.stringify(props.datasets));
    }

    return {
        organisations: organisationList,
        organisationCounts: counts,
        selectOrganisation: addOrganisation,
        deselectOrganisation: removeOrganisation,
        clearOrganisations: clearOrganisations,
        filteredDatasets: filteredDatasetList,
        selectedOrganisations: selectedOrganisations,
        filteredCount: props.datasets.length - filteredDatasetList.length,
    };
};
