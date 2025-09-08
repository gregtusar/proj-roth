import React from 'react';
import { FormControl } from 'baseui/form-control';
import { Input, SIZE as InputSize } from 'baseui/input';
import { Textarea } from 'baseui/textarea';
import { Select, TYPE } from 'baseui/select';
import { Checkbox, STYLE_TYPE, LABEL_PLACEMENT } from 'baseui/checkbox';
import { RadioGroup, Radio } from 'baseui/radio';
import { DatePicker } from 'baseui/datepicker';
import { TimePicker } from 'baseui/timepicker';
import { Slider } from 'baseui/slider';
import { Button, KIND, SIZE, SHAPE } from 'baseui/button';
import { FileUploader } from 'baseui/file-uploader';
import { PhoneInput, COUNTRIES } from 'baseui/phone-input';
import { PaymentCard } from 'baseui/payment-card';
import { styled } from 'baseui';
import { tokens } from '../../theme/customTheme';
import { FieldLabel } from './Typography';

// Re-export all Base UI form components
export {
  FormControl,
  Input,
  InputSize,
  Textarea,
  Select,
  TYPE as SelectType,
  Checkbox,
  STYLE_TYPE as CheckboxStyle,
  LABEL_PLACEMENT as LabelPlacement,
  RadioGroup,
  Radio,
  DatePicker,
  TimePicker,
  Slider,
  Button,
  KIND as ButtonKind,
  SIZE as ButtonSize,
  SHAPE as ButtonShape,
  FileUploader,
  PhoneInput,
  COUNTRIES,
  PaymentCard,
};

// Form layout components
export const Form = styled('form', {
  display: 'flex',
  flexDirection: 'column',
  gap: tokens.spacing.scale600,
});

export const FormRow = styled('div', {
  display: 'flex',
  gap: tokens.spacing.scale600,
  '@media (max-width: 768px)': {
    flexDirection: 'column',
  },
});

export const FormColumn = styled('div', {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  gap: tokens.spacing.scale600,
});

export const FormSection = styled('fieldset', ({ $theme }) => ({
  border: `1px solid ${$theme.colors.borderOpaque}`,
  borderRadius: tokens.borders.radius400,
  padding: tokens.spacing.scale700,
  marginBottom: tokens.spacing.scale600,
}));

export const FormSectionTitle = styled('legend', ({ $theme }) => ({
  padding: `0 ${tokens.spacing.scale400}`,
  fontSize: '16px',
  fontWeight: 500,
  color: $theme.colors.contentPrimary,
}));

// Enhanced form field component
interface FormFieldProps {
  label: string;
  caption?: string;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  caption,
  error,
  required,
  disabled,
  children,
}) => {
  return (
    <FormControl
      label={() => (
        <FieldLabel>
          {label}
          {required && <span style={{ color: 'red' }}> *</span>}
        </FieldLabel>
      )}
      caption={caption}
      error={error}
      disabled={disabled}
    >
      {children}
    </FormControl>
  );
};

// Common form patterns
interface TextFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  caption?: string;
  size?: 'default' | 'compact' | 'large';
}

export const TextField: React.FC<TextFieldProps> = ({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  error,
  required,
  disabled,
  caption,
  size = 'default',
}) => {
  return (
    <FormField
      label={label}
      error={error}
      required={required}
      disabled={disabled}
      caption={caption}
    >
      <Input
        value={value}
        onChange={e => onChange(e.currentTarget.value)}
        placeholder={placeholder}
        type={type}
        size={size}
        error={!!error}
        disabled={disabled}
      />
    </FormField>
  );
};

interface TextAreaFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  caption?: string;
  maxLength?: number;
}

export const TextAreaField: React.FC<TextAreaFieldProps> = ({
  label,
  value,
  onChange,
  placeholder,
  rows = 4,
  error,
  required,
  disabled,
  caption,
  maxLength,
}) => {
  return (
    <FormField
      label={label}
      error={error}
      required={required}
      disabled={disabled}
      caption={caption}
    >
      <Textarea
        value={value}
        onChange={e => onChange(e.currentTarget.value)}
        placeholder={placeholder}
        rows={rows}
        error={!!error}
        disabled={disabled}
        maxLength={maxLength}
      />
    </FormField>
  );
};

interface SelectFieldProps {
  label: string;
  value: any[];
  onChange: (value: any[]) => void;
  options: Array<{ label: string; id: string | number }>;
  placeholder?: string;
  multi?: boolean;
  searchable?: boolean;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  caption?: string;
}

export const SelectField: React.FC<SelectFieldProps> = ({
  label,
  value,
  onChange,
  options,
  placeholder = 'Select...',
  multi = false,
  searchable = true,
  error,
  required,
  disabled,
  caption,
}) => {
  return (
    <FormField
      label={label}
      error={error}
      required={required}
      disabled={disabled}
      caption={caption}
    >
      <Select
        value={value}
        onChange={({ value }) => onChange(value as any)}
        options={options}
        placeholder={placeholder}
        multi={multi}
        searchable={searchable}
        error={!!error}
        disabled={disabled}
      />
    </FormField>
  );
};

interface CheckboxFieldProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  caption?: string;
  disabled?: boolean;
  indeterminate?: boolean;
}

export const CheckboxField: React.FC<CheckboxFieldProps> = ({
  label,
  checked,
  onChange,
  caption,
  disabled,
  indeterminate,
}) => {
  return (
    <Checkbox
      checked={checked}
      onChange={e => onChange(e.currentTarget.checked)}
      disabled={disabled}
      isIndeterminate={indeterminate}
    >
      <div>
        <FieldLabel>{label}</FieldLabel>
        {caption && <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>{caption}</div>}
      </div>
    </Checkbox>
  );
};

// Form buttons
export const FormActions = styled('div', {
  display: 'flex',
  gap: tokens.spacing.scale400,
  justifyContent: 'flex-end',
  marginTop: tokens.spacing.scale700,
  paddingTop: tokens.spacing.scale600,
  borderTop: '1px solid',
  borderColor: 'inherit',
});

export const SubmitButton: React.FC<{
  children: React.ReactNode;
  onClick?: () => void;
  loading?: boolean;
  disabled?: boolean;
}> = ({ children, onClick, loading, disabled }) => (
  <Button
    type="submit"
    onClick={onClick}
    isLoading={loading}
    disabled={disabled}
  >
    {children}
  </Button>
);

export const CancelButton: React.FC<{
  children: React.ReactNode;
  onClick: () => void;
}> = ({ children, onClick }) => (
  <Button
    type="button"
    kind={KIND.secondary}
    onClick={onClick}
  >
    {children}
  </Button>
);

// Form validation helpers
export const validateEmail = (email: string): string | null => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email) return 'Email is required';
  if (!emailRegex.test(email)) return 'Invalid email format';
  return null;
};

export const validatePhone = (phone: string): string | null => {
  const phoneRegex = /^\+?[\d\s-()]+$/;
  if (!phone) return 'Phone number is required';
  if (!phoneRegex.test(phone)) return 'Invalid phone format';
  if (phone.replace(/\D/g, '').length < 10) return 'Phone number too short';
  return null;
};

export const validateRequired = (value: any, fieldName: string): string | null => {
  if (!value || (typeof value === 'string' && !value.trim())) {
    return `${fieldName} is required`;
  }
  return null;
};

export const validateMinLength = (value: string, minLength: number, fieldName: string): string | null => {
  if (value.length < minLength) {
    return `${fieldName} must be at least ${minLength} characters`;
  }
  return null;
};

export const validateMaxLength = (value: string, maxLength: number, fieldName: string): string | null => {
  if (value.length > maxLength) {
    return `${fieldName} must be no more than ${maxLength} characters`;
  }
  return null;
};