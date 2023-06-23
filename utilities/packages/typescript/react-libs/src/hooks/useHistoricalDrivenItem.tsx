import { DomainInfoBase, ItemBase } from "../shared-interfaces/RegistryModels";

interface DetermineLatestIdInput {
    item: ItemBase;
}
interface DetermineLatestIdOutput {
    id?: number;
}
function determineLatestId(
    inputs: DetermineLatestIdInput
): DetermineLatestIdOutput {
    /**
    Function: DetermineLatestId

    Determines the latest ID from the given historical item if relevant.
    */

    const history = inputs.item.history;
    return { id: history.length > 0 ? history[0].id : undefined };
}

interface GetHistoryItemByIdInput {
    item: ItemBase;
    id: number;
}
interface GetHistoryItemByIdOutput {
    info?: DomainInfoBase;
}
function getHistoryItemById(
    inputs: GetHistoryItemByIdInput
): GetHistoryItemByIdOutput {
    /**
    Function: GetHistoryItemById

    Returns the domain info of the item in history by ID. Returns undefined if the item is not present
    */

    return {
        info: inputs.item.history.find((entry) => {
            return entry.id === inputs.id;
        })?.item,
    };
}

interface CreateItemInput<T> {
    item: T;
    info: DomainInfoBase;
}
interface CreateItemOutput<T> {
    item: T;
}
function createItem<T>(inputs: CreateItemInput<T>): CreateItemOutput<T> {
    /**
    Function: createItem
    
    Accepts the base item + domain info and creates a full item base
    */

    // Unpack the original item then spread the updated domain info over it
    const newItem: T = { ...inputs.item, ...inputs.info };
    // Ensure that keys
    return { item: newItem };
}

export interface UseHistoricalDrivenItemProps<T extends ItemBase> {
    item?: T;
    historicalId?: number;
}

interface ErrorInfo {
    // Error state if relevant
    error: boolean;
    errorMessage?: string;
}

// Some default error states

// no error
const noError: ErrorInfo = {
    error: false,
    errorMessage: undefined,
};

// Empty history
const emptyHistory: ErrorInfo = {
    error: true,
    errorMessage: "The history array was empty.",
};

// missing id
const cantFindIdError = (id: number): ErrorInfo => {
    return {
        error: true,
        errorMessage: `Cannot find history item with ID ${id}`,
    };
};
export interface UseHistoricalDrivenItemOutput<T> extends ErrorInfo {
    currentItem?: T;
    latestItem?: T;
    latestId?: number;
    isLatest?: boolean;
}

export function useHistoricalDrivenItem<T extends ItemBase>(
    props: UseHistoricalDrivenItemProps<T>
): UseHistoricalDrivenItemOutput<T> {
    /**
    Hook: useHistoricalDrivenItem

    Takes a potentially defined item as input + optionally a driven historical
    item choice and provides the current checked out version, the latest
    version and whether the current checked out version is latest.

    */

    // Determine the if provided is latest

    // If the input is undefined - then just return no data
    if (props.item === undefined) {
        return { ...noError };
    }

    // Else - we have a defined/loaded item - so we can process it
    const { id: latestId } = determineLatestId({ item: props.item });

    // We couldn't find a latest ID from the history - something is wrong - just
    // return current item and no info about latest
    if (latestId === undefined) {
        return { currentItem: props.item, ...emptyHistory };
    }

    // Get item by id
    const { info: latestDomainInfo } = getHistoryItemById({
        item: props.item,
        id: latestId,
    });

    // If the latest item isn't defined this means something went wrong - just return current item and no info about latest
    if (latestDomainInfo === undefined) {
        return {
            currentItem: props.item,
            ...cantFindIdError(latestId),
        };
    }

    // We have the latest entry, and we have the latest item - if driven we
    // should find that item and check if it's the most recent

    var isLatest = false;
    var currentItem: undefined | T = undefined;
    // if we are being driven then find current id
    if (props.historicalId !== undefined) {
        // current item is latest - just return it
        if (props.historicalId === latestId) {
            isLatest = true;
            currentItem = props.item;
        } else {
            // Not latest in this case
            isLatest = false;

            // We need to replace the data here with driven version
            const { info: currentDomainInfo } = getHistoryItemById({
                item: props.item,
                id: props.historicalId,
            });

            if (currentDomainInfo === undefined) {
                // Something went wrong here - error state?
                return {
                    currentItem: props.item,
                    ...cantFindIdError(props.historicalId),
                };
            } else {
                // Success state
                currentItem = createItem<T>({
                    item: props.item,
                    info: currentDomainInfo,
                }).item;
            }
        }
    }

    // if we are not driven - then just use the latest and return info we have
    else {
        isLatest = true;
        currentItem = props.item;
    }

    // Return current item, latest item and whether the current item is the latest
    return {
        currentItem: currentItem,
        latestItem: createItem<T>({
            item: props.item,
            info: latestDomainInfo,
        }).item,
        latestId: latestId,
        isLatest: isLatest,
        ...noError,
    };
}
