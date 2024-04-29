import debounce from "lodash.debounce";
import { useCallback, useLayoutEffect, useRef, useState } from "react";

export interface UseObservedRefProps {
  debug?: boolean;
}
export interface UseObservedRefOutput {
  callbackRef: ReturnType<typeof useCallback>;
  dims: {
    width: number | undefined;
    height: number | undefined;
  };
}
export const useObservedRef = (
  props: UseObservedRefProps,
): UseObservedRefOutput => {
  /**
    Hook: useObservedRef

    Sets up a managed div ref which observes the height and width with a
    debounced size observer and manages cleanup using a useLayoutEffect cleanup 
    */

  // Debug log
  const debugMode = props.debug ?? false;

  const conditionalLog = (message: string) => {
    if (debugMode) {
      console.log("useObservedRef: " + message);
    }
  };

  conditionalLog("Rendering custom hook.");

  // Ref for managing the element
  const ref = useRef<HTMLDivElement | null>(null);

  // Width and height state
  const [height, setHeight] = useState<number | undefined>(undefined);
  const [width, setWidth] = useState<number | undefined>(undefined);

  // Callback ref to update the ref
  const callbackRef = useCallback((node) => {
    conditionalLog("Callback ref fired.");

    // Update the div ref manually so we can manage the resize observer
    // lifecycle in a cleanup layout effect hook
    ref.current = node;
    if (node) {
      conditionalLog("Node was defined in callback ref.");
      setHeight(node.clientHeight);
      setWidth(node.clientWidth);
    }
  }, []);

  useLayoutEffect(() => {
    // When the svg div ref is mounted we can setup a resize observer
    // including a cleanup function

    conditionalLog("Use layout effect which observes internal ref fired.");

    // Pullout current canvas ref as node
    const node = ref.current;

    // Setup a observer for width - runs on div size change - height is
    // manually controlled
    if (node) {
      conditionalLog("Node was defined in use layout effect hook");
      const resizeObserver = new ResizeObserver(
        // Debounce the update to avoid excessive rerenders
        debounce(
          () => {
            conditionalLog("ResizeObserver fired.");
            if (node) {
              conditionalLog("Node defined in ResizeObserver.");
              conditionalLog(
                `Height: ${node.clientHeight}, Width: ${node.clientWidth}.`,
              );
              setHeight(node.clientHeight);
              setWidth(node.clientWidth);
            }
          },
          200, //ms
        ),
      );
      // Observe the html element
      resizeObserver.observe(node);

      conditionalLog("Observer established.");
      // Clean up
      return () => {
        resizeObserver.disconnect();
        conditionalLog("Observer cleaned up.");
      };
    }
  }, [ref.current]);

  return {
    callbackRef,
    dims: {
      width,
      height,
    },
  };
};
