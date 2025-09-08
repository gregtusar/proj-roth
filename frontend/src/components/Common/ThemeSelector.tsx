import React from 'react';
import { Select, TYPE } from 'baseui/select';
import { styled } from 'baseui';
import { ThemeType } from '../../theme/customTheme';
import { LabelMedium } from './Typography';
import { tokens } from '../../theme/customTheme';

const Container = styled('div', {
  display: 'flex',
  alignItems: 'center',
  gap: tokens.spacing.scale600,
});

const ThemePreview = styled<'div', { $themeType: ThemeType }>('div', ({ $themeType }) => {
  const getColors = () => {
    switch ($themeType) {
      case ThemeType.LIGHT:
        return {
          bg: '#ffffff',
          text: '#1a1a1a',
          accent: '#1a73e8',
        };
      case ThemeType.DARK:
        return {
          bg: '#1a1a1a',
          text: '#e5e7eb',
          accent: '#4285f4',
        };
      case ThemeType.TERMINAL:
        return {
          bg: '#0a0a0a',
          text: '#00ff00',
          accent: '#ffb000',
        };
      default:
        return {
          bg: '#ffffff',
          text: '#1a1a1a',
          accent: '#1a73e8',
        };
    }
  };

  const colors = getColors();

  return {
    width: '24px',
    height: '24px',
    borderRadius: '4px',
    border: `2px solid ${colors.accent}`,
    background: `linear-gradient(135deg, ${colors.bg} 50%, ${colors.text} 50%)`,
    marginRight: tokens.spacing.scale300,
    boxShadow: $themeType === ThemeType.TERMINAL ? `0 0 5px ${colors.accent}` : 'none',
  };
});

const OptionContent = styled('div', {
  display: 'flex',
  alignItems: 'center',
});

interface ThemeSelectorProps {
  size?: 'default' | 'compact' | 'large' | 'mini';
  showLabel?: boolean;
}

const themeOptions = [
  {
    id: ThemeType.LIGHT,
    label: 'Light',
    description: 'Clean and professional',
  },
  {
    id: ThemeType.DARK,
    label: 'Dark',
    description: 'Modern dark theme',
  },
  {
    id: ThemeType.TERMINAL,
    label: 'Terminal',
    description: 'Hacker mode with green text',
  },
];

const ThemeSelector: React.FC<ThemeSelectorProps> = ({ 
  size = 'default',
  showLabel = true 
}) => {
  const [currentTheme, setCurrentTheme] = React.useState<ThemeType>(() => {
    const stored = localStorage.getItem('theme');
    return (stored as ThemeType) || ThemeType.LIGHT;
  });

  const handleThemeChange = (params: any) => {
    if (params.value.length > 0) {
      const newTheme = params.value[0].id as ThemeType;
      setCurrentTheme(newTheme);
      localStorage.setItem('theme', newTheme);
      
      // Dispatch custom event for theme change
      window.dispatchEvent(new Event('themeChange'));
      
      // Also dispatch storage event for other tabs
      window.dispatchEvent(new StorageEvent('storage', {
        key: 'theme',
        newValue: newTheme,
        url: window.location.href,
      }));
    }
  };

  const selectedOption = themeOptions.find(opt => opt.id === currentTheme);

  return (
    <Container>
      {showLabel && <LabelMedium>Theme:</LabelMedium>}
      <Select
        size={size as any}
        type={TYPE.select}
        options={themeOptions}
        value={selectedOption ? [selectedOption] : []}
        onChange={handleThemeChange}
        clearable={false}
        searchable={false}
        placeholder="Select theme"
        overrides={{
          Root: {
            style: {
              width: size === 'compact' ? '140px' : '180px',
            },
          },
          ValueContainer: {
            component: ({ children, ...props }: any) => (
              <div {...props}>
                <OptionContent>
                  <ThemePreview $themeType={currentTheme} />
                  {children}
                </OptionContent>
              </div>
            ),
          },
          OptionContent: {
            component: ({ option, ...props }: any) => (
              <div {...props}>
                <OptionContent>
                  <ThemePreview $themeType={option.id as ThemeType} />
                  <div>
                    <div style={{ fontWeight: 500 }}>{option.label}</div>
                    <div style={{ fontSize: '11px', opacity: 0.7 }}>{option.description}</div>
                  </div>
                </OptionContent>
              </div>
            ),
          },
        }}
      />
    </Container>
  );
};

export default ThemeSelector;

// Export a mini version for navbar
export const MiniThemeSelector: React.FC = () => {
  return <ThemeSelector size="compact" showLabel={false} />;
};