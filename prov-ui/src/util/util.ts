import { Buffer } from "buffer";
import { HTTPValidationError, Detail } from "../shared-interfaces/APIResponses";

export const parseJwt = (token: string) => {
    var base64Payload = token.split(".")[1];
    var payload = Buffer.from(base64Payload, "base64");
    return JSON.parse(payload.toString());
};

export const objectIsEmpty = (obj: Object) => {
    return Object.keys(obj).length === 0;
};

export const displayValidationError = (valError: HTTPValidationError) => {
    var messageList: string[] = [];
    let errors = valError.detail;
    errors.forEach((detail: Detail) => {
        messageList.push(
            `[Message: ${detail.msg}, Type: ${
                detail.type
            }, Location: ${detail.loc.join(" - ")}]`
        );
    });
    return messageList.join(", ");
};

const vowelRegex = "^[aieouAIEOU].*";

export const startsWithVowel = (word: string): boolean => {
    return !!word.match(vowelRegex);
};

export const timestampToLocalTime = (timestamp: number): string => {
    /**
    Converts a seconds based timestamp to a local string based on browser time
    zone.

    Falls back to using the timestamp directly in case of parsing error.
     */

    // Try parsing times
    var outputString: string = timestamp.toString();
    try {
        outputString = new Date(timestamp * 1000).toLocaleString(undefined, {
            timeZoneName: "shortGeneric",
        });
    } catch (e: any) {
        console.log(
            `Failed to parse time with error ${e} falling back to unparsed string.`
        );
    }
    return outputString;
};

export const prettifyTitle = (input: string): string => {
    let splitString = input.split(/(?=[A-Z])/);
    return splitString.join(" ");
};

export const prettifyRecordName = (propertyName: string) => {
    return propertyName
        .split("_")
        .map((el: string) => {
            let capitalized = el.charAt(0).toUpperCase() + el.slice(1);
            return capitalized;
        })
        .join(" ");
};

export function parseTime(timestamp: number): string {
    // Convert to milliseconds
    const date = new Date(timestamp * 1000);
    // Format to string in browser local timezone
    return date.toLocaleString();
}

export function stripPossibleFullStop(input: string): string {
    /**
        Strips either "." or '."' from the end of a string so that error
        messages don't duplicate full stops.

     */
    const trimmed = input.trimRight();
    if (trimmed.endsWith(".")) {
        return trimmed.slice(0, trimmed.length - 1);
    } else if (trimmed.endsWith('."')) {
        return trimmed.slice(0, trimmed.length - 2) + '"';
    } else {
        return trimmed;
    }
}

export const composeSectionHeaderTitle = (
    parentField: string | undefined,
    recordName: string
) => {
    if (!isNaN(Number(recordName))) {
        recordName = (Number(recordName) + 1).toString();
    }
    let composedName = recordName;
    if (parentField) {
        if (parentField.charAt(parentField.length - 1) === "s") {
            parentField = parentField.slice(0, parentField.length - 1);
        }
        composedName = `${prettifyRecordName(parentField)} ${recordName}`;
    }
    return composedName;
};

// The prioritisedProperties list defines the properties that will be at the top of the view and also the order of those items
export const prioritisedProperties: string[] = [
    "id",
    "workflow_template_id",
    "display_name",
    "description",
    "record_type",
    "updated_timestamp",
    "created_timestamp",
    "s3",
];

// These fields will be removed non destructively from the item being displayed
export const strippedProperties: string[] = [
    "history",
    "item_category",
    "item_subtype",
    "record_type",
];

// This method fixes the order of properties in the entity object
// so that they are listed appropriately in the item view
export const reorderProperties = (item: any) => {
    let reorderedItem: any = {};

    prioritisedProperties.forEach((p) => {
        Object.keys(item).forEach((k) => {
            if (k === p) {
                reorderedItem[k] = item[k];
            }
        });
    });

    Object.keys(item).forEach((k) => {
        if (!prioritisedProperties.includes(k)) {
            reorderedItem[k] = item[k];
        }
        if (item[k] && !Array.isArray(item[k]) && typeof item[k] === "object") {
            reorderedItem[k] = reorderProperties(item[k]);
        }
    });
    return reorderedItem;
};

export const stripProperties = (item: any) => {
    const newItem = JSON.parse(JSON.stringify(item));
    for (const prop of strippedProperties) {
        delete newItem[prop];
    }
    return newItem;
};

export const prepareObject = (item: any) => {
    return reorderProperties(stripProperties(item));
};

export const createSubtypeAcronym = (subtype: string) => {
    return subtype
        .split("_")
        .map((word) => word.toLowerCase()[0].toUpperCase())
        .join(" ");
};
