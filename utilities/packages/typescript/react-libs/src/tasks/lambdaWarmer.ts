import { WARMER_API_URL } from "../queries/endpoints";

export class Warmer {
    warm = () => {
        console.log("Initiating lambda warm up @ ", WARMER_API_URL);

        // Data store, auth api, search
        fetch(WARMER_API_URL)
            .then((resp: any) => {
                console.log("Warmed up APIs");
            })
            .catch((e: any) => {
                console.log("Warm up failed. Error: " + e);
            });
    };

    constructor() {
        this.warm();
        const warmTimeoutMinutes = 2;
        const warmTimeoutMs = warmTimeoutMinutes * 60 * 1000;
        setInterval(this.warm, warmTimeoutMs);
    }
}
