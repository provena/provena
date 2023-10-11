// BASED ON https://github.com/tlinhart/s3-browser (heavily modified)
import { ListObjectsV2Command, S3Client } from "@aws-sdk/client-s3";
import { Link, Theme } from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import { DataGrid, GridColDef, GridToolbar } from "@mui/x-data-grid";
import { useQuery } from "@tanstack/react-query";
import { usePresignedUrl } from "hooks/generatePresignedUrl";
import prettyBytes from "pretty-bytes";
import { useState } from "react";
import { Credentials } from "react-libs/shared-interfaces/DataStoreAPI";
import { copyToClipboard, initiateDownload } from "util/helper";
import BriefPopup, { PopupColors } from "./BriefPopup";
import { ThreeDotMenu } from "./ThreeDotMenu";
import DownloadIcon from "@mui/icons-material/Download";

const AWS_REGION = "ap-southeast-2";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        // Data grid list
        dataGrid: {
            width: "100%",
        },
        // Other useful layout
        fullWidth: { width: "100%" },
        tbPaddings: {
            paddingTop: theme.spacing(2),
            paddingBottom: theme.spacing(2),
        },
        lrPadding: {
            paddingLeft: theme.spacing(2),
            paddingRight: theme.spacing(2),
        },
    })
);

function oneStepUp(path: string): string {
    // Remove trailing "/"
    if (path.endsWith("/")) {
        path = path.slice(0, -1);
    }

    // Split the path by "/"
    const segments = path.split("/");

    // If there's only one segment, return an empty string or a root symbol
    if (segments.length === 1) {
        return "";
    }

    // Remove the last segment
    segments.pop();

    // Join the segments back together with "/"
    const newPath = segments.join("/") + "/";

    return newPath;
}

const s3VisColumnDefs: GridColDef[] = [
    {
        field: "name",
        headerName: "Name",
        // Fixed width
        flex: 1,
        // at least 50
        minWidth: 75,
        renderCell(params) {
            return params.value;
        },
    },
    {
        field: "lastModified",
        headerName: "Last Modified",
        // Fixed width
        width: 200,
    },
    {
        field: "size",
        headerName: "Size",
        // Fixed width
        width: 120,
    },
    {
        field: "actions",
        headerName: "Actions",
        width: 100,
        renderCell(params) {
            return params.value;
        },
    },
];
interface S3VizRowContent {
    id: string;
    name: string | JSX.Element;
    lastModified: string;
    size: string;
    actions: string | JSX.Element;
}

interface VisualiseS3ComponentProps {
    // Used to help form copy strings
    bucketName: string;
    items: S3Items;
    onNavigateTo: (prefix: string) => void;
    displayPopup: (message: string, color: PopupColors) => void;
    getPresignedUrl: (
        path: string,
        onSuccess: (url: string) => void,
        showMessage: boolean | undefined
    ) => void;
}

const VisualiseS3Component = (props: VisualiseS3ComponentProps) => {
    /**
    Component: VisualiseS3Component

    Uses a MUI data grid to visualise S3 file system
    
    */
    // Data grid table columns render
    const classes = useStyles();

    // Set data grid table
    const defaultPageSize: number = 5;
    const [pageSize, setPageSize] = useState<number>(defaultPageSize);

    var rows: S3VizRowContent[] = props.items.folders.map((item) => {
        return {
            id: item.name,
            name: (
                <Link
                    onClick={() => {
                        props.onNavigateTo(item.path);
                    }}
                    style={{
                        cursor: "pointer",
                    }}
                >
                    {item.name}
                </Link>
            ),
            size: "-",
            lastModified: "-",
            actions: (
                <ThreeDotMenu
                    items={[
                        {
                            label: "Copy S3 URI",
                            action: () => {
                                copyToClipboard(
                                    `s3://${props.bucketName}/${item.path}`
                                );
                                props.displayPopup(
                                    "Copied object path to clipboard!",
                                    "success"
                                );
                            },
                            key: "copy",
                        },
                    ]}
                />
            ),
        };
    });

    rows = rows.concat(
        props.items.objects.map((item) => {
            return {
                id: item.name,
                name: item.name,
                size: prettyBytes(item.size),
                lastModified: item.lastModified.toLocaleString(),
                actions: (
                    <ThreeDotMenu
                        items={[
                            {
                                label: "Copy S3 URI",
                                action: () => {
                                    copyToClipboard(
                                        `s3://${props.bucketName}/${item.path}`
                                    );
                                    props.displayPopup(
                                        "Copied folder path to clipboard!",
                                        "success"
                                    );
                                },
                                key: "copy",
                            },
                            {
                                label: "Copy Presigned URL",
                                action: () => {
                                    props.getPresignedUrl(
                                        item.path,
                                        (url) => {
                                            copyToClipboard(url);
                                            props.displayPopup(
                                                "Copied presigned URL to clipboard!",
                                                "success"
                                            );
                                        },
                                        true
                                    );
                                },
                                key: "presign",
                            },
                            {
                                label: (
                                    <>
                                        Download{" "}
                                        <DownloadIcon
                                            style={{ marginLeft: "20px" }}
                                        />
                                    </>
                                ),
                                action: () => {
                                    props.getPresignedUrl(
                                        item.path,
                                        (url) => {
                                            // Let user know download is initiating
                                            props.displayPopup(
                                                "Starting download...",
                                                "success"
                                            );
                                            // Once URL is generated - download it
                                            initiateDownload(url, item.name);
                                        },
                                        false
                                    );
                                    props.displayPopup(
                                        "Preparing file download...",
                                        "inProgress"
                                    );
                                },
                                key: "download",
                            },
                        ]}
                    />
                ),
            } as S3VizRowContent;
        })
    );
    console.log(rows);

    return (
        <div style={{ height: "420px" }}>
            <DataGrid
                columns={s3VisColumnDefs}
                rows={rows}
                pageSize={pageSize}
                disableColumnFilter
                disableColumnSelector
                disableDensitySelector
                rowsPerPageOptions={[5, 10, 20]}
                onPageSizeChange={(size) => {
                    setPageSize(size);
                }}
                disableSelectionOnClick
                getRowHeight={() => 50}
                components={{
                    Toolbar: GridToolbar,
                    //NoRowsOverlay: NoRowsOverlayText,
                }}
                componentsProps={{
                    toolbar: {
                        csvOptions: { disableToolbarButton: true },
                        printOptions: { disableToolbarButton: true },
                        showQuickFilter: true,
                    },
                }}
                className={classes.dataGrid}
            />
        </div>
    );
};

interface Folder {
    name: string;
    path: string;
}

interface Object {
    name: string;
    lastModified: Date;
    size: number;
    path: string;
}

interface S3Items {
    folders: Folder[];
    objects: Object[];
}

async function listContents(
    bucket: string,
    prefix: string,
    credentials: Credentials
): Promise<S3Items> {
    const region = AWS_REGION;
    const s3Client = new S3Client({
        region,
        credentials: {
            accessKeyId: credentials.aws_access_key_id,
            secretAccessKey: credentials.aws_secret_access_key,
            sessionToken: credentials.aws_session_token,
        },
    });

    console.log({
        Bucket: bucket,
        Prefix: prefix,
        Delimiter: "/",
    });

    const data = await s3Client.send(
        new ListObjectsV2Command({
            Bucket: bucket,
            Prefix: prefix,
            Delimiter: "/",
        })
    );
    console.log(data);
    return {
        folders:
            data.CommonPrefixes?.map(({ Prefix }: any) => ({
                name: Prefix.slice(prefix.length),
                path: Prefix,
            })) || [],
        objects:
            data.Contents?.filter(({ Key }) => {
                return Key !== prefix;
            }).map(({ Key, LastModified, Size }: any) => ({
                name: Key.slice(prefix.length),
                lastModified: LastModified,
                size: Size,
                path: Key,
            })) || [],
    };
}

function useContents(inputs: {
    bucket: string;
    prefix: string;
    credentials: Credentials;
}) {
    const { bucket, prefix, credentials } = inputs;
    return useQuery({
        queryKey: ["contents", prefix],
        queryFn: () => listContents(bucket, prefix, credentials),
    });
}

interface ExplorerProps {
    datasetId: string;
    bucket: string;
    prefix: string;
    credentials: Credentials;
}

export function S3Explorer(props: ExplorerProps) {
    const { bucket, prefix: startingPrefix, credentials } = props;
    const [prefix, setPrefix] = useState<string>(startingPrefix);

    return (
        <S3Listing
            datasetId={props.datasetId}
            rootPrefix={startingPrefix}
            bucket={bucket}
            prefix={prefix}
            credentials={credentials}
            setPrefix={setPrefix}
        />
    );
}

interface S3ListingProps {
    datasetId: string;
    bucket: string;
    prefix: string;
    credentials: Credentials;
    rootPrefix: string;
    setPrefix: (prefix: string) => void;
}

function S3Listing(props: S3ListingProps) {
    const { prefix, bucket, credentials } = props;
    const { status, data, error } = useContents({
        bucket,
        prefix,
        credentials,
    });

    // Manage popup state
    const [presignPopupOpen, setPresignPopupOpen] = useState<boolean>(false);
    const [presignMessage, setPresignMessage] = useState<string>("");
    const [popupColor, setPopupColor] = useState<PopupColors>("success");

    const showPopup = (message: string, color: PopupColors = "success") => {
        setPopupColor(color);
        setPresignMessage(message);
        // just toggle a refresh of the timer - kind of hacky
        setPresignPopupOpen(false);
        setPresignPopupOpen(true);
    };

    // Mutator for generating presigned urls
    const presign = usePresignedUrl();

    // This adds a fake folder item if we aren't at the root to enable
    // navigation up one level
    const parentItem: Folder | undefined =
        prefix.length > props.rootPrefix.length
            ? {
                  name: "...",
                  path: oneStepUp(prefix),
              }
            : undefined;

    return (
        <>
            <BriefPopup
                message={presignMessage}
                open={presignPopupOpen}
                handleClose={() => {
                    setPresignPopupOpen(false);
                }}
                color={popupColor}
            />
            <VisualiseS3Component
                items={{
                    folders: [
                        ...(parentItem ? [parentItem] : []),
                        ...(data?.folders ?? []),
                    ],
                    objects: data?.objects ?? [],
                }}
                onNavigateTo={(path: string) => {
                    props.setPrefix(path);
                }}
                displayPopup={showPopup}
                bucketName={props.bucket}
                getPresignedUrl={(
                    path: string,
                    onSuccess: (url: string) => void,
                    showMessage: boolean | undefined
                ) => {
                    presign.mutate(
                        {
                            datasetId: props.datasetId,
                            path: path.slice(props.rootPrefix.length),
                        },
                        {
                            onSuccess: (res) => {
                                onSuccess(res.presigned_url);
                            },
                        }
                    );
                    if (showMessage ?? true) {
                        showPopup("Generating presigned URL...", "inProgress");
                    }
                }}
            />
        </>
    );
}
