import React from "react";
import { useLocation } from "react-router-dom";

export function useQString() {
    /**
     * Wraps parsing of q string from location router v5
     */
    const { search } = useLocation();
    return React.useMemo(() => new URLSearchParams(search), [search]);
}
