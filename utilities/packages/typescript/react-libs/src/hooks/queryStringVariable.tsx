import { useEffect, useState } from "react";
import { useHistory } from "react-router-dom";

interface useQueryStringVariableProps {
    queryStringKey: string;
    defaultValue?: string;
    readOnly?: boolean;
}
interface useQueryStringVariableResponse {
    value: string | undefined;
    setValue?: (searchQuery: string | undefined) => void;
}
export const useQueryStringVariable = (
    props: useQueryStringVariableProps
): useQueryStringVariableResponse => {
    /**
    Hook: useQueryStringVariable
    */

    const readOnly = props.readOnly !== undefined ? props.readOnly : false;

    if (props.queryStringKey === "") {
        throw new Error("Provided an empty query string key!");
    }

    // Get the search query if present from search params
    const history = useHistory();
    const location = history.location;

    // Pull out current query string and set default if relevant
    const params = new URLSearchParams(location.search);
    const definedQuery = params.get(props.queryStringKey) ?? props.defaultValue;

    const [value, setValue] = useState<string | undefined>(
        definedQuery ?? undefined
    );

    useEffect(() => {
        if (value !== undefined && value !== "") {
            // Update
            const currentLocation = history.location;
            const updatedParams = new URLSearchParams(currentLocation.search);
            updatedParams.set(props.queryStringKey, value);
            const searchString = updatedParams.toString();
            currentLocation.search = searchString;
            history.replace(currentLocation);
        } else {
            // Clear
            const currentLocation = history.location;
            const updatedParams = new URLSearchParams(currentLocation.search);
            updatedParams.delete(props.queryStringKey);
            const searchString = updatedParams.toString();
            currentLocation.search = searchString;
            history.replace(currentLocation);
        }
    }, [value]);

    return {
        value: value,
        setValue: readOnly ? undefined : setValue,
    };
};

export interface UseTypedQueryStringVariableProps<DataType extends string> {
    queryStringKey: string;
    defaultValue: DataType | undefined;
    readOnly?: boolean;
}
export interface UseTypedQueryStringVariableOutput<DataType extends string> {
    value: DataType | undefined;
    setValue?: (value: DataType | undefined) => void;
}
export function useTypedQueryStringVariable<DataType extends string>(
    props: UseTypedQueryStringVariableProps<DataType>
): UseTypedQueryStringVariableOutput<DataType> {
    /**
    Hook: useTypedQueryStringVariable
    
    Manages a typed query string argument. 

    Must extend string type to enable safe casting to qstring arg.
    */

    const readOnly = props.readOnly !== undefined ? props.readOnly : false;

    if (props.queryStringKey === "") {
        throw new Error("Provided an empty query string key!");
    }

    // Get the search query if present from search params
    const history = useHistory();
    const location = history.location;

    // Pull out current query string and set default if relevant
    const params = new URLSearchParams(location.search);
    const existingValue =
        params.get(props.queryStringKey) ?? props.defaultValue;

    // Slightly risky cast to type
    // TODO could be improved with list of valid values
    const [value, setValue] = useState<DataType | undefined>(
        existingValue ? (existingValue as DataType) : undefined
    );

    useEffect(() => {
        if (value !== undefined && value !== "") {
            // Update
            const currentLocation = history.location;
            const updatedParams = new URLSearchParams(currentLocation.search);
            updatedParams.set(props.queryStringKey, value);
            const searchString = updatedParams.toString();
            currentLocation.search = searchString;
            history.replace(currentLocation);
        } else {
            // Clear
            const currentLocation = history.location;
            const updatedParams = new URLSearchParams(currentLocation.search);
            updatedParams.delete(props.queryStringKey);
            const searchString = updatedParams.toString();
            currentLocation.search = searchString;
            history.replace(currentLocation);
        }
    }, [value]);

    return {
        value: value,
        setValue: readOnly ? undefined : setValue,
    };
}
