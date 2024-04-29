import {
  Checkbox,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
} from "@mui/material";
import { Theme } from "@mui/material/styles";

import createStyles from "@mui/styles/createStyles";
import { useLoadedSubtypes, ResultMap } from "react-libs";
import makeStyles from "@mui/styles/makeStyles";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      display: "flex",
      flexDirection: "column",
      padding: theme.spacing(1),
      "& li": {
        listStyleType: "none",
      },
    },
  }),
);

interface OrganisationFilterDisplayProps {
  organisationIdList: string[];
  count: Map<string, number>;
  filteredCount: number;
  selectedOrganisations: string[];
  addOrganisation: (org: string) => void;
  removeOrganisation: (org: string) => void;
}

export const OrganisationFilterDisplay = (
  props: OrganisationFilterDisplayProps,
) => {
  const classes = useStyles();

  const getOrganisationLabel = (orgId: string, orgMap: ResultMap) => {
    // count part
    const countInt = props.count.get(orgId);
    const countStr = `[${countInt}]`;
    // try to get the organisation from map
    const possibleOrgResult = orgMap.get(orgId);

    var orgDisplay = "";
    if (possibleOrgResult === undefined) {
      // For whatever reason the resolution hasn't resolved this org - fall back to ID
      orgDisplay = orgId;
    } else {
      // loading?
      if (possibleOrgResult.loading) {
        orgDisplay = "Loading...";
      } else if (possibleOrgResult.error) {
        orgDisplay = `Failed to load ${orgId}...`;
      } else {
        orgDisplay =
          possibleOrgResult?.data?.display_name ?? `Failed to load ${orgId}...`;
      }
    }

    return `${orgDisplay} ${countStr}`;
  };
  // Download the details of the list of organisations
  const { results: resolvedOrgMap } = useLoadedSubtypes({
    ids: props.organisationIdList,
    subtype: "ORGANISATION",
  });

  return (
    <div className={classes.root}>
      <h3>Apply Filters</h3>
      <FormControl>
        <FormLabel component="h3">Organizations</FormLabel>
        <FormGroup>
          {props.organisationIdList.map((org) => {
            const included = props.selectedOrganisations.includes(org);
            return (
              <li key={org}>
                <FormControlLabel
                  control={
                    <Checkbox
                      size="small"
                      checked={included}
                      onChange={() => {
                        if (included) {
                          // remove
                          props.removeOrganisation(org);
                        } else {
                          // add
                          props.addOrganisation(org);
                        }
                      }}
                      name={org}
                    />
                  }
                  label={getOrganisationLabel(org, resolvedOrgMap)}
                />
              </li>
            );
          })}
        </FormGroup>
        <p>
          Filtering{" "}
          {props.filteredCount === 0 ? (
            props.filteredCount
          ) : (
            <b>{props.filteredCount}</b>
          )}{" "}
          entries...
        </p>
      </FormControl>
    </div>
  );
};
