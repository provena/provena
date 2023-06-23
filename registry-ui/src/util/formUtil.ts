import { FieldProps } from "@rjsf/utils";

interface DeriveTitleAndDescriptionInput<T> extends FieldProps<T> {
    fallthroughDescription: string;
    fallthroughTitle: string;
}
interface DeriveTitleAndDescriptionOutput {
    title: string;
    description: string;
}
export function deriveTitleAndDescription<T>(
    inputs: DeriveTitleAndDescriptionInput<T>
): DeriveTitleAndDescriptionOutput {
    /**
    Function: DeriveTitleAndDescription
    
    Derives a form title and description by falling through from 

    1) ui schema
    2) json schema 
    3) provided default
    */
    return {
        title:
            (inputs.uiSchema?.["ui:title"] as string | undefined) ??
            inputs.schema.title ??
            inputs.fallThroughDescription,
        description:
            (inputs.uiSchema?.["ui:description"] as string | undefined) ??
            inputs.schema.description ??
            inputs.fallThroughDescription,
    };
}
