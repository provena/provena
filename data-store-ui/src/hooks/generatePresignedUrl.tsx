import { useMutation } from "@tanstack/react-query";
import { GetPresignedUrlInputs, getPresignedUrl } from "react-libs";

export const usePresignedUrl = () => {
    /**
    Hook: usePresignedUrl

    */
    return useMutation({
        mutationFn: (inputs: GetPresignedUrlInputs) => {
            return getPresignedUrl(inputs);
        },
        onSuccess: (_, variables) => {
            console.log("Signed " + variables.path + " successfully.");
        },
    });
};
