import AccountTreeIcon from "@mui/icons-material/AccountTree";
import DataArrayIcon from "@mui/icons-material/DataArray";
import DonutSmallIcon from "@mui/icons-material/DonutSmall";
import GradingIcon from "@mui/icons-material/Grading";
import GroupsIcon from "@mui/icons-material/Groups";
import ModelTrainingIcon from "@mui/icons-material/ModelTraining";
import MultilineChartIcon from "@mui/icons-material/MultilineChart";
import PersonIcon from "@mui/icons-material/Person";
import StickyNote2Icon from "@mui/icons-material/StickyNote2";
import TerminalIcon from "@mui/icons-material/Terminal";
import TimelapseIcon from "@mui/icons-material/Timelapse";
import AutoGraph from "@mui/icons-material/AutoGraph";
import Update from "@mui/icons-material/Update";
import { ItemSubType } from "../provena-interfaces/RegistryAPI";

export interface Swatch {
  colour: string;
  tintColour: string;
  shadeColour: string;
}

export interface SwatchCollection {
  personSwatch: Swatch;
  organisationSwatch: Swatch;
  datasetSwatch: Swatch;
  datasetTemplateSwatch: Swatch;
  modelSwatch: Swatch;
  modelRunSwatch: Swatch;
  modelRunWorkflowDefinitionSwatch: Swatch;
  workflowRunSwatch: Swatch;
  qualifiedAssociationSwatch: Swatch;
  softwareSwatch: Swatch;
  workflowDefinitonSwatch: Swatch;
  createSwatch: Swatch;
  versionSwatch: Swatch;
  studySwatch: Swatch;
  defaultSwatch: Swatch;
}

export const Swatches: SwatchCollection = {
  personSwatch: {
    colour: "#c83813",
    tintColour: "#ed613d",
    shadeColour: "#92290e",
  },
  organisationSwatch: {
    colour: "#40abac",
    tintColour: "#70c9ca",
    shadeColour: "#308081",
  },
  datasetSwatch: {
    colour: "#753b52",
    tintColour: "#a95577",
    shadeColour: "#4e2737",
  },
  datasetTemplateSwatch: {
    colour: "#c6762d",
    tintColour: "#dc9e65",
    shadeColour: "#965922",
  },
  modelSwatch: {
    colour: "#104080",
    tintColour: "#1963c6",
    shadeColour: "#09264c",
  },
  modelRunSwatch: {
    colour: "#3c1679",
    tintColour: "#5d22bb",
    shadeColour: "#230d47",
  },
  modelRunWorkflowDefinitionSwatch: {
    colour: "#9f248d",
    tintColour: "#d33ebd",
    shadeColour: "#6f1962",
  },
  workflowRunSwatch: {
    colour: "#38212e",
    tintColour: "#693e57",
    shadeColour: "#130b10",
  },
  qualifiedAssociationSwatch: {
    colour: "#8a7262",
    tintColour: "#ae9a8d",
    shadeColour: "#68564a",
  },
  softwareSwatch: {
    colour: "#948b8c",
    tintColour: "#bab4b4",
    shadeColour: "#776d6e",
  },
  workflowDefinitonSwatch: {
    colour: "#3b6d34",
    tintColour: "#58a24d",
    shadeColour: "#254521",
  },
  createSwatch: {
    colour: "#3f6a6b",
    tintColour: "#779495",
    shadeColour: "#233f3f",
  },
  versionSwatch: {
    colour: "#8a508f",
    tintColour: "#ad83b0",
    shadeColour: "#653969",
  },
  studySwatch: {
    colour: "#03adfc",
    tintColour: "#6fccf7",
    shadeColour: "#1b8bbf",
  },
  defaultSwatch: {
    colour: "#500778",
    tintColour: "#810bc2",
    shadeColour: "#2b0440",
  },
};

export const getSwatchForSubtype = (subtype: ItemSubType | undefined) => {
  let baseSwatch: Swatch;
  switch (subtype) {
    case "DATASET":
      baseSwatch = Swatches.datasetSwatch;
      break;
    case "DATASET_TEMPLATE":
      baseSwatch = Swatches.datasetTemplateSwatch;
      break;
    case "MODEL":
      baseSwatch = Swatches.modelSwatch;
      break;
    case "MODEL_RUN":
      baseSwatch = Swatches.modelRunSwatch;
      break;
    case "MODEL_RUN_WORKFLOW_TEMPLATE":
      baseSwatch = Swatches.modelRunWorkflowDefinitionSwatch;
      break;
    case "ORGANISATION":
      baseSwatch = Swatches.organisationSwatch;
      break;
    case "PERSON":
      baseSwatch = Swatches.personSwatch;
      break;
    case "SOFTWARE":
      baseSwatch = Swatches.softwareSwatch;
      break;
    case "WORKFLOW_TEMPLATE":
      baseSwatch = Swatches.workflowDefinitonSwatch;
      break;
    case "WORKFLOW_RUN":
      baseSwatch = Swatches.workflowDefinitonSwatch;
      break;
    case "CREATE":
      baseSwatch = Swatches.createSwatch;
      break;
    case "VERSION":
      baseSwatch = Swatches.versionSwatch;
      break;
    case "STUDY":
      baseSwatch = Swatches.studySwatch;
      break;
    default:
      baseSwatch = Swatches.defaultSwatch;
      break;
  }
  return baseSwatch;
};

export const assignIcon = (
  subType: ItemSubType | undefined,
  specifiedClass: string,
) => {
  if (subType === undefined) {
    return null;
  }

  switch (subType) {
    case "DATASET":
      return <DonutSmallIcon className={specifiedClass} />;
    case "DATASET_TEMPLATE":
      return <DataArrayIcon className={specifiedClass} />;
    case "MODEL":
      return <MultilineChartIcon className={specifiedClass} />;
    case "MODEL_RUN":
      return <ModelTrainingIcon className={specifiedClass} />;
    case "MODEL_RUN_WORKFLOW_TEMPLATE":
      return <AccountTreeIcon className={specifiedClass} />;
    case "CREATE":
      return <AutoGraph className={specifiedClass} />;
    case "VERSION":
      return <Update className={specifiedClass} />;
    case "ORGANISATION":
      return <GroupsIcon className={specifiedClass} />;
    case "PERSON":
      return <PersonIcon className={specifiedClass} />;
    case "SOFTWARE":
      return <TerminalIcon className={specifiedClass} />;
    case "WORKFLOW_TEMPLATE":
      return <GradingIcon className={specifiedClass} />;
    case "WORKFLOW_RUN":
      return <TimelapseIcon className={specifiedClass} />;
    case "STUDY":
      return <StickyNote2Icon className={specifiedClass} />;
    default:
      return null;
  }
};

export const mapSubTypeToPrettyName = (subType?: ItemSubType) => {
  let resultArray = subType?.split("_");
  let result = "";
  if (resultArray === undefined || resultArray.length == 0) return result;
  resultArray.forEach((r) => {
    result += r[0];
    result += r.slice(1).toLowerCase();
    if (resultArray!.indexOf(r) != resultArray!.length - 1) {
      result += " ";
    }
  });
  return result;
};
