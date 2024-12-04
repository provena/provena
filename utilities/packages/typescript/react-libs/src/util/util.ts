import { FieldProps } from "@rjsf/utils";
import { Buffer } from "buffer";
import unset from "lodash.unset";
import { REGISTRY_LINK } from "../queries";
import {
  Detail,
  HTTPValidationError,
} from "../provena-interfaces/APIResponses";
import { ItemSubType } from "../provena-interfaces/RegistryModels";
import { StatusResponse } from "../provena-interfaces/SharedTypes";

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
  const trimmed = input.trimEnd();
  if (trimmed.endsWith(".")) {
    return trimmed.slice(0, trimmed.length - 1);
  } else if (trimmed.endsWith('."')) {
    return trimmed.slice(0, trimmed.length - 2) + '"';
  } else {
    return trimmed;
  }
}
// How do we encode registry deep links?
const registryRecordsPrefix = "records";
const filteringQString = "filtering";
const subtypeQString = "subtype";

export const generateRegistryDeepLink = (
  subtypeFilter: ItemSubType | undefined
) => {
  /**
   * Generates a deep link into the registry explore view optionally tailored
   * to a subtype
   */
  return `${REGISTRY_LINK}/${registryRecordsPrefix}?${filteringQString}=${
    subtypeFilter !== undefined ? "true" : "false"
  }${
    subtypeFilter !== undefined
      ? "&" + subtypeQString + "=" + subtypeFilter
      : ""
  }`;
};

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
  // Study fields
  "title",
  "description",
  "owner_username",
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

const stripProperties = (item: any) => {
  const newItem = JSON.parse(JSON.stringify(item));
  for (const prop of strippedProperties) {
    // Using unset allows deletion of nested properties
    unset(newItem, prop);
  }
  return newItem;
};

export const prepareObject = (item: any) => {
  return reorderProperties(stripProperties(item));
};

export function requestErrToMsg(err: any): string {
  // Attempt to determine UI friendly status and err from error message
  console.log("Decoding error", err);

  // Attempt parsing as status response
  try {
    let jsonStatus = err as StatusResponse;
    let details = jsonStatus.status.details;
    if (!!details) {
      return details;
    } else {
      throw new Error("Failed to parse repsonse as StatusResponse.");
    }
  } catch {
    try {
      // Attempt parsing as either axios response object or axios complete err
      // object

      // These are fall back errs
      var statusCode = "Unknown";
      var message = "Unknown - contact admin and check console";

      // Try decoding from response object (as in status code err)
      const response = err.response;
      if (response !== undefined) {
        try {
          statusCode = response.status;
        } catch {}

        try {
          message = response.data.detail ? response.data.detail : "";
        } catch {}
      } else {
        // Try decoding directly from response object
        try {
          statusCode = err.status;
        } catch {}

        try {
          message = err.data.detail[0].msg
            ? err.data.detail[0].msg
            : err.data.detail
            ? err.data.detail
            : "";
        } catch {}
      }
    } catch {
      message = "Unknown error during fetch.";
      statusCode = "500";
    }

    const msg = `Status code ${statusCode}. Error message: ${message}`;
    console.log("Error message: " + msg);
    return msg;
  }
}

export async function readErrorFromFileBlob(error: any): Promise<string> {
  /* This helper functions allows you to read JSON content that is 
  sent from the server when there are errors in generating/downloading 
  files. Axios only allows one 'responseType', hence a blob file needs 
  to be read and converted to JSON to retrieve the error message sent 
  from the server */ 
  
  let error_message = "Something has gone wrong with generating your file."
   
  if (error.data) {
      try {
          const file = await error.data.text()
          // Extract the "detail" field.
          const { detail } = JSON.parse(file)
          error_message = detail
      } catch (convertError) {
        console.log("Failed to decode error from server.")
        // Keep default error message if conversion fails
      }
  }

  return error_message
}

interface FormTitleDescription {
  title: string;
  description: string;
}
export function deriveTitleDescription<T>(
  props: FieldProps<T>
): FormTitleDescription {
  const uiTitle = props.uiSchema ? props.uiSchema["ui:title"] : undefined;
  const uiDescription = props.uiSchema
    ? props.uiSchema["ui:description"]
    : undefined;

  const title = uiTitle ?? props.schema.title ?? "Untitled";
  const description = uiDescription ?? props.schema.description ?? "";

  return {
    title,
    description,
  };
}

export const createSubtypeAcronym = (subtype: string) => {
  return subtype
    .split("_")
    .map((word) => word.toLowerCase()[0].toUpperCase())
    .join(" ");
};

// Check if input string is empty
export const isBlank = (str: string): boolean => {
  const blankReg = new RegExp(/^\s*$/);
  return !str || blankReg.test(str);
};

export const allDefined = (inputs: any[]): boolean => {
  return !inputs.some((i) => i === undefined || i === null);
};

type DeepCopyResult = { [key: string]: any } | any[] | any;

export function filteredNoneDeepCopy(input: any): DeepCopyResult {
  // If input is an object (but not null)
  if (typeof input === "object" && input !== null) {
    // If it's an array
    if (Array.isArray(input)) {
      return input
        .filter((item) => item != null)
        .map((item) => filteredNoneDeepCopy(item));
    }
    // If it's a regular object
    else {
      const newObj: { [key: string]: any } = {};
      for (const [key, value] of Object.entries(input)) {
        if (value != null && value !== "null") {
          newObj[key] = filteredNoneDeepCopy(value);
        }
      }
      return newObj;
    }
  }
  // If it's a primitive value
  return input;
}