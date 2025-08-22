import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { styled } from 'baseui';
import { Heading, HeadingLevel } from 'baseui/heading';
import { Checkbox, LABEL_PLACEMENT } from 'baseui/checkbox';
import { Button, KIND, SIZE } from 'baseui/button';
import { RootState, AppDispatch } from '../../store';
import { toggleDarkMode } from '../../store/settingsSlice';

const Container = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  height: '100%',
  backgroundColor: $isDarkMode ? '#1a1a1a' : '#f5f5f5',
  padding: '32px',
  transition: 'background-color 0.3s ease',
}));

const Card = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  backgroundColor: $isDarkMode ? '#2d2d2d' : '#ffffff',
  borderRadius: '12px',
  padding: '24px',
  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
  maxWidth: '800px',
  margin: '0 auto',
  transition: 'background-color 0.3s ease',
}));

const Section = styled('div', {
  marginBottom: '32px',
});

const SectionTitle = styled('h3', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  fontSize: '18px',
  fontWeight: '600',
  marginBottom: '16px',
  color: $isDarkMode ? '#ffffff' : '#111827',
  transition: 'color 0.3s ease',
}));

const SectionDescription = styled('p', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  fontSize: '14px',
  color: $isDarkMode ? '#a0a0a0' : '#6b7280',
  marginBottom: '20px',
  transition: 'color 0.3s ease',
}));

const SettingRow = styled('div', {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '12px 0',
  borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
});

const SettingLabel = styled('label', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  fontSize: '14px',
  fontWeight: '500',
  color: $isDarkMode ? '#e0e0e0' : '#374151',
  flex: 1,
  transition: 'color 0.3s ease',
}));

const SettingDescription = styled('span', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  fontSize: '12px',
  color: $isDarkMode ? '#808080' : '#9ca3af',
  display: 'block',
  marginTop: '4px',
  transition: 'color 0.3s ease',
}));

const ButtonContainer = styled('div', {
  display: 'flex',
  justifyContent: 'flex-end',
  marginTop: '24px',
});

const Settings: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { isDarkMode } = useSelector((state: RootState) => state.settings);

  const handleDarkModeToggle = () => {
    dispatch(toggleDarkMode());
  };

  const handleDismiss = () => {
    navigate(-1); // Go back to previous page
  };

  return (
    <Container $isDarkMode={isDarkMode}>
      <HeadingLevel>
        <Heading 
          styleLevel={3} 
          overrides={{
            Block: {
              style: {
                color: isDarkMode ? '#ffffff' : '#111827',
                marginBottom: '24px',
                transition: 'color 0.3s ease',
              },
            },
          }}
        >
          Settings
        </Heading>
      </HeadingLevel>

      <Card $isDarkMode={isDarkMode}>
        <Section>
          <SectionTitle $isDarkMode={isDarkMode}>Appearance</SectionTitle>
          <SectionDescription $isDarkMode={isDarkMode}>
            Customize the look and feel of your workspace
          </SectionDescription>
          
          <SettingRow>
            <div style={{ flex: 1 }}>
              <SettingLabel $isDarkMode={isDarkMode}>
                Dark Mode
                <SettingDescription $isDarkMode={isDarkMode}>
                  Switch between light and dark themes
                </SettingDescription>
              </SettingLabel>
            </div>
            <Checkbox
              checked={isDarkMode}
              onChange={handleDarkModeToggle}
              labelPlacement={LABEL_PLACEMENT.right}
              overrides={{
                Root: {
                  style: {
                    alignItems: 'center',
                  },
                },
                Checkmark: {
                  style: {
                    backgroundColor: isDarkMode ? '#3b82f6' : undefined,
                    borderColor: isDarkMode ? '#3b82f6' : undefined,
                  },
                },
                Label: {
                  style: {
                    color: isDarkMode ? '#e0e0e0' : '#374151',
                    fontSize: '14px',
                  },
                },
              }}
            >
              {isDarkMode ? 'Enabled' : 'Disabled'}
            </Checkbox>
          </SettingRow>
        </Section>

        <Section>
          <SectionTitle $isDarkMode={isDarkMode}>Notifications</SectionTitle>
          <SectionDescription $isDarkMode={isDarkMode}>
            Manage your notification preferences
          </SectionDescription>
          
          <SettingRow>
            <div style={{ flex: 1 }}>
              <SettingLabel $isDarkMode={isDarkMode}>
                Email Notifications
                <SettingDescription $isDarkMode={isDarkMode}>
                  Receive updates about your lists and queries
                </SettingDescription>
              </SettingLabel>
            </div>
            <Checkbox
              checked={false}
              labelPlacement={LABEL_PLACEMENT.right}
              overrides={{
                Label: {
                  style: {
                    color: isDarkMode ? '#e0e0e0' : '#374151',
                    fontSize: '14px',
                  },
                },
              }}
              disabled
            >
              Coming Soon
            </Checkbox>
          </SettingRow>
        </Section>

        <Section>
          <SectionTitle $isDarkMode={isDarkMode}>Data & Privacy</SectionTitle>
          <SectionDescription $isDarkMode={isDarkMode}>
            Manage your data and privacy settings
          </SectionDescription>
          
          <SettingRow>
            <div style={{ flex: 1 }}>
              <SettingLabel $isDarkMode={isDarkMode}>
                Data Export
                <SettingDescription $isDarkMode={isDarkMode}>
                  Export your lists and query history
                </SettingDescription>
              </SettingLabel>
            </div>
            <Checkbox
              checked={false}
              labelPlacement={LABEL_PLACEMENT.right}
              overrides={{
                Label: {
                  style: {
                    color: isDarkMode ? '#e0e0e0' : '#374151',
                    fontSize: '14px',
                  },
                },
              }}
              disabled
            >
              Coming Soon
            </Checkbox>
          </SettingRow>
        </Section>

        <ButtonContainer>
          <Button
            onClick={handleDismiss}
            kind={KIND.secondary}
            size={SIZE.large}
            overrides={{
              BaseButton: {
                style: {
                  backgroundColor: isDarkMode ? '#404040' : '#e5e7eb',
                  color: isDarkMode ? '#ffffff' : '#374151',
                  ':hover': {
                    backgroundColor: isDarkMode ? '#525252' : '#d1d5db',
                  },
                },
              },
            }}
          >
            Dismiss
          </Button>
        </ButtonContainer>
      </Card>
    </Container>
  );
};

export default Settings;