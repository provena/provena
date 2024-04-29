import { useUserLinkServiceLookup } from "../hooks/useUserLinkServiceLookup";
import {
  JsonDetailViewComponent,
  JsonDetailViewComponentProps,
} from "./JsonRenderer/JsonDetailView";

interface LinkedUsernameDisplayComponentProps {
  // What is the username?
  username: string;

  // What are the props - only styling is used but in the future we might use
  // more
  jsonProps: JsonDetailViewComponentProps;
}
export const LinkedUsernameDisplayComponent = (
  props: LinkedUsernameDisplayComponentProps,
) => {
  /**
    Component: LinkedUsernameDisplayComponent
    
    Shows a linked username stylised with a copyable linked handle where appropriate
    */
  const link = useUserLinkServiceLookup({ username: props.username });

  const showLink = !link.loading && !link.error && link.data !== undefined;
  const linkedId = link.data;
  // const loadedPerson = person.data?.item as ItemPerson | undefined;

  var objContents: { [k: string]: string } = {
    username: props.username,
  };

  if (showLink) {
    // Need to specify an override for the linked person ID
    objContents["linked_person_id"] = linkedId!;
  }

  return (
    <JsonDetailViewComponent
      json={{ name: undefined, value: objContents }}
      style={props.jsonProps.style}
      context={props.jsonProps.context}
    />
  );
};
