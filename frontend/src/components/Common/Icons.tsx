import React from 'react';
import {
  Alert,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Check,
  CheckIndeterminate,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Delete,
  DeleteAlt,
  Filter,
  Grab,
  Hide,
  Menu,
  Overflow,
  Plus,
  Search,
  Show,
  Spinner,
  TriangleDown,
  TriangleLeft,
  TriangleRight,
  TriangleUp,
  Upload,
} from 'baseui/icon';

// Re-export all Base UI icons
export {
  Alert,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Check,
  CheckIndeterminate,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Delete,
  DeleteAlt,
  Filter,
  Grab,
  Hide,
  Menu,
  Overflow,
  Plus,
  Search,
  Show,
  Spinner,
  TriangleDown,
  TriangleLeft,
  TriangleRight,
  TriangleUp,
  Upload,
};

// Icon mapping for easier migration from other icon libraries
// Maps common icon names to Base UI equivalents

// MUI Icons mapping
export const FlashOnIcon = Alert; // Using Alert as placeholder
export const PsychologyIcon = Alert; // Using Alert as placeholder
export const BalanceIcon = Alert; // Using Alert as placeholder
export const RocketLaunchIcon = ArrowUp; // Using ArrowUp as placeholder
export const RefreshIcon = Spinner;
export const DownloadIcon = ArrowDown;
export const SendIcon = ArrowRight;
export const EmailIcon = Alert; // Using Alert as placeholder
export const VisibilityIcon = Show;
export const ContentCopyIcon = Alert; // Using Alert as placeholder
export const LinkIcon = Alert; // Using Alert as placeholder
export const LinkOffIcon = Alert; // Using Alert as placeholder
export const CompareArrowsIcon = ArrowRight; // Using ArrowRight as placeholder

// Heroicons mapping
export const XMarkIcon = Delete;
export const PencilIcon = Alert; // Using Alert as placeholder
export const CheckIcon = Check;
export const XCircleIcon = DeleteAlt;
export const PlusIcon = Plus;
export const DocumentTextIcon = Alert; // Using Alert as placeholder
export const ClockIcon = Spinner; // Using Spinner as placeholder
export const ArrowTopRightOnSquareIcon = ArrowUp;
export const TrashIcon = Delete;
export const DocumentPlusIcon = Plus;

// Lucide React mapping
export const Terminal = Alert; // Using Alert as placeholder

// Custom icon component with consistent sizing
interface IconProps {
  size?: 'small' | 'medium' | 'large' | number;
  color?: string;
  title?: string;
  overrides?: any;
}

const sizeMap = {
  small: 16,
  medium: 24,
  large: 32,
};

export const Icon: React.FC<{ icon: React.ComponentType<any> } & IconProps> = ({
  icon: IconComponent,
  size = 'medium',
  color,
  title,
  overrides,
}) => {
  const iconSize = typeof size === 'string' ? sizeMap[size] : size;
  
  return (
    <IconComponent
      size={iconSize}
      color={color}
      title={title}
      overrides={overrides}
    />
  );
};

// Commonly used icon compositions
export const LoadingSpinner: React.FC<{ size?: IconProps['size'] }> = ({ size = 'medium' }) => (
  <Spinner $size={typeof size === 'string' ? sizeMap[size] : size} />
);

export const SuccessIcon: React.FC<{ size?: IconProps['size'] }> = ({ size = 'medium' }) => (
  <Check size={typeof size === 'string' ? sizeMap[size] : size} color="positive" />
);

export const ErrorIcon: React.FC<{ size?: IconProps['size'] }> = ({ size = 'medium' }) => (
  <Alert size={typeof size === 'string' ? sizeMap[size] : size} color="negative" />
);

export const InfoIcon: React.FC<{ size?: IconProps['size'] }> = ({ size = 'medium' }) => (
  <Alert size={typeof size === 'string' ? sizeMap[size] : size} color="primary" />
);

export const WarningIcon: React.FC<{ size?: IconProps['size'] }> = ({ size = 'medium' }) => (
  <Alert size={typeof size === 'string' ? sizeMap[size] : size} color="warning" />
);