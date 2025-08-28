import React from "react";
import { Alert, AlertTitle, Box, IconButton } from "@mui/material";
import { Warning, Close } from "@mui/icons-material";

export interface WarningBannerProps {
  /**
   * The warning message to display
   */
  message: string;
  /**
   * Optional title for the warning banner
   */
  title?: string;
  /**
   * Whether the banner can be dismissed by the user
   * @default false
   */
  dismissible?: boolean;
  /**
   * Callback function when banner is dismissed
   */
  onDismiss?: () => void;
  /**
   * Whether to show the warning icon
   * @default true
   */
  showIcon?: boolean;
  /**
   * Custom severity level
   * @default 'warning'
   */
  severity?: "error" | "warning" | "info" | "success";
  /**
   * Additional CSS class name
   */
  className?: string;
}

export const WarningBanner: React.FC<WarningBannerProps> = ({
  message,
  title,
  dismissible = false,
  onDismiss,
  showIcon = true,
  severity = "warning",
  className,
  children,
}) => {
  const [isVisible, setIsVisible] = React.useState(true);

  const handleDismiss = () => {
    setIsVisible(false);
    if (onDismiss) {
      onDismiss();
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div>
      <Box
        sx={{
          position: "sticky",
          top: 0,
          zIndex: 9999, // Higher than most MUI components
          width: "100%",
          height: 75,
        }}
        className={className}
      >
        <Alert
          severity={severity}
          icon={showIcon ? <Warning /> : false}
          action={
            dismissible ? (
              <IconButton
                aria-label="close"
                color="inherit"
                size="small"
                onClick={handleDismiss}
              >
                <Close fontSize="inherit" />
              </IconButton>
            ) : null
          }
          sx={{
            borderRadius: 0, // Remove rounded corners for full-width appearance
            "& .MuiAlert-message": {
              width: "100%",
            },
          }}
        >
          {title && <AlertTitle>{title}</AlertTitle>}
          {message}
        </Alert>
      </Box>
      {children}
    </div>
  );
};
