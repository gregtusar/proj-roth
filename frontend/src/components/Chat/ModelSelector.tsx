import React from 'react';
import {
  FormControl,
  Select,
  MenuItem,
  Box,
  Typography,
  Tooltip,
  Chip
} from '@mui/material';
import { styled } from '@mui/material/styles';
import FlashOnIcon from '@mui/icons-material/FlashOn';
import PsychologyIcon from '@mui/icons-material/Psychology';
import BalanceIcon from '@mui/icons-material/Balance';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';

const StyledSelect = styled(Select)(({ theme }) => ({
  minWidth: 200,
  '& .MuiSelect-select': {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing(1),
    paddingTop: theme.spacing(1),
    paddingBottom: theme.spacing(1),
  },
}));

const ModelOption = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1.5),
  width: '100%',
}));

export interface ModelConfig {
  id: string;
  name: string;
  displayName: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  speed: 'fast' | 'medium' | 'slow';
  capability: 'basic' | 'advanced' | 'experimental';
}

export const AVAILABLE_MODELS: ModelConfig[] = [
  {
    id: 'gemini-2.0-flash-exp',
    name: 'Flash',
    displayName: 'Fast',
    description: 'Quick responses for simple queries and list generation',
    icon: <FlashOnIcon />,
    color: '#FFA726',
    speed: 'fast',
    capability: 'basic'
  },
  {
    id: 'gemini-1.5-flash-002',
    name: 'Flash-002',
    displayName: 'Balanced',
    description: 'Good balance of speed and capability',
    icon: <BalanceIcon />,
    color: '#66BB6A',
    speed: 'medium',
    capability: 'advanced'
  },
  {
    id: 'gemini-1.5-pro-002',
    name: 'Pro',
    displayName: 'Smart',
    description: 'Advanced analysis and complex reasoning',
    icon: <PsychologyIcon />,
    color: '#5C6BC0',
    speed: 'slow',
    capability: 'advanced'
  },
  {
    id: 'gemini-2.0-flash-thinking-exp',
    name: 'Thinking',
    displayName: 'Experimental',
    description: 'Experimental model with chain-of-thought reasoning',
    icon: <RocketLaunchIcon />,
    color: '#AB47BC',
    speed: 'medium',
    capability: 'experimental'
  }
];

interface ModelSelectorProps {
  value: string;
  onChange: (modelId: string) => void;
  disabled?: boolean;
  showDescription?: boolean;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({
  value,
  onChange,
  disabled = false,
  showDescription = true
}) => {

  const handleChange = (event: any) => {
    onChange(event.target.value);
  };

  const renderValue = (value: unknown) => {
    const model = AVAILABLE_MODELS.find(m => m.id === value);
    if (!model) return value as React.ReactNode;

    return (
      <ModelOption>
        <Box sx={{ color: model.color, display: 'flex', alignItems: 'center' }}>
          {model.icon}
        </Box>
        <Typography variant="body2" fontWeight="medium">
          {model.displayName}
        </Typography>
        {model.capability === 'experimental' && (
          <Chip 
            label="Beta" 
            size="small" 
            color="secondary" 
            sx={{ height: 18, fontSize: '0.7rem' }}
          />
        )}
      </ModelOption>
    );
  };

  return (
    <FormControl size="small">
      <StyledSelect
        value={value}
        onChange={handleChange}
        disabled={disabled}
        renderValue={renderValue}
        displayEmpty
      >
        {AVAILABLE_MODELS.map((model) => (
          <MenuItem key={model.id} value={model.id}>
            <Tooltip 
              title={model.description} 
              placement="right"
              disableHoverListener={!showDescription}
            >
              <ModelOption>
                <Box sx={{ 
                  color: model.color, 
                  display: 'flex', 
                  alignItems: 'center',
                  minWidth: 24
                }}>
                  {model.icon}
                </Box>
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="body2" fontWeight="medium">
                    {model.displayName}
                  </Typography>
                  {showDescription && (
                    <Typography variant="caption" color="text.secondary">
                      {model.name} • {model.speed === 'fast' ? 'Fast' : model.speed === 'medium' ? 'Balanced' : 'Slower'}
                    </Typography>
                  )}
                </Box>
                {model.capability === 'experimental' && (
                  <Chip 
                    label="Beta" 
                    size="small" 
                    color="secondary" 
                    sx={{ height: 18, fontSize: '0.7rem' }}
                  />
                )}
              </ModelOption>
            </Tooltip>
          </MenuItem>
        ))}
      </StyledSelect>
    </FormControl>
  );
};

export default ModelSelector;