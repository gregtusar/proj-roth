import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { styled } from 'baseui';
import { Heading, HeadingLevel } from 'baseui/heading';
import { Checkbox, LABEL_PLACEMENT } from 'baseui/checkbox';
import { Button, KIND, SIZE } from 'baseui/button';
import { Textarea } from 'baseui/textarea';
import { Notification, KIND as NotificationKind } from 'baseui/notification';
import { RootState, AppDispatch } from '../../store';
import { toggleDarkMode } from '../../store/settingsSlice';
import * as settingsService from '../../services/settings';

const Container = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  height: '100%',
  backgroundColor: $isDarkMode ? '#1a1a1a' : '#f5f5f5',
  padding: '32px',
  transition: 'background-color 0.3s ease',
  overflowY: 'auto',
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
  const { user } = useSelector((state: RootState) => state.auth);
  
  const [customPrompt, setCustomPrompt] = useState('');
  const [originalPrompt, setOriginalPrompt] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [notification, setNotification] = useState<{
    message: string;
    kind: typeof NotificationKind[keyof typeof NotificationKind];
  } | null>(null);

  useEffect(() => {
    // Load user's custom prompt when component mounts
    loadCustomPrompt();
  }, []);

  const loadCustomPrompt = async () => {
    try {
      console.log('[Settings] Loading custom prompt...');
      const settings = await settingsService.getSettings();
      console.log('[Settings] Received settings:', settings);
      
      if (settings && settings.custom_prompt) {
        console.log('[Settings] Setting custom prompt:', settings.custom_prompt);
        setCustomPrompt(settings.custom_prompt);
        setOriginalPrompt(settings.custom_prompt);
      } else {
        console.log('[Settings] No custom prompt found in settings');
        setCustomPrompt('');
        setOriginalPrompt('');
      }
    } catch (error) {
      console.error('[Settings] Error loading custom prompt:', error);
      setNotification({
        message: 'Failed to load custom prompt',
        kind: NotificationKind.negative,
      });
      setTimeout(() => setNotification(null), 3000);
    }
  };

  const handleSavePrompt = async () => {
    setIsSaving(true);
    try {
      await settingsService.saveCustomPrompt(customPrompt);
      setOriginalPrompt(customPrompt);
      setNotification({
        message: 'Custom prompt saved successfully!',
        kind: NotificationKind.positive,
      });
      setTimeout(() => setNotification(null), 3000);
    } catch (error) {
      console.error('Error saving custom prompt:', error);
      setNotification({
        message: 'Failed to save custom prompt',
        kind: NotificationKind.negative,
      });
    } finally {
      setIsSaving(false);
    }
  };

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
          <SectionTitle $isDarkMode={isDarkMode}>Custom System Prompt</SectionTitle>
          <SectionDescription $isDarkMode={isDarkMode}>
            Add custom instructions that will be appended to the system prompt for all your conversations
          </SectionDescription>
          
          <Textarea
            value={customPrompt}
            onChange={(e) => setCustomPrompt((e.target as HTMLTextAreaElement).value)}
            placeholder="Enter custom instructions here... (e.g., 'Always include demographic breakdowns', 'Focus on Union County')"
            rows={12}
            disabled={isSaving}
            overrides={{
              Root: {
                style: {
                  marginBottom: '12px',
                },
              },
              Input: {
                style: {
                  backgroundColor: isDarkMode ? '#1a1a1a' : '#ffffff',
                  color: isDarkMode ? '#e0e0e0' : '#111827',
                  borderColor: isDarkMode ? '#404040' : '#d1d5db',
                  fontSize: '16px',
                  lineHeight: '1.5',
                },
              },
            }}
          />
          
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '12px'
          }}>
            <span style={{ 
              fontSize: '12px', 
              color: isDarkMode ? '#808080' : '#9ca3af'
            }}>
              {customPrompt.length} characters
            </span>
            
            <div style={{ display: 'flex', gap: '8px' }}>
              {customPrompt !== originalPrompt && (
                <Button
                  onClick={() => setCustomPrompt(originalPrompt)}
                  disabled={isSaving}
                  kind={KIND.secondary}
                  size={SIZE.compact}
                >
                  Reset
                </Button>
              )}
              
              <Button
                onClick={handleSavePrompt}
                disabled={customPrompt === originalPrompt || isSaving}
                kind={KIND.primary}
                size={SIZE.compact}
                isLoading={isSaving}
              >
                Save Prompt
              </Button>
            </div>
          </div>
          
          {notification && notification.message === 'Custom prompt saved successfully!' && (
            <div style={{
              marginTop: '8px',
              fontSize: '14px',
              color: '#10b981',
              textAlign: 'right'
            }}>
              ✓ Prompt saved
            </div>
          )}
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