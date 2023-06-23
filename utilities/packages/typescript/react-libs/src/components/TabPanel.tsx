interface TabPanelProps {
    children: React.ReactNode;
    index: number | string;
    currentIndex: number | string;
}

export const TabPanel = (props: TabPanelProps) => (
    <div hidden={props.currentIndex !== props.index} key={props.index}>
        {props.currentIndex === props.index && <>{props.children}</>}
    </div>
);
