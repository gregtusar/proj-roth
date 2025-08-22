import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Button, SIZE, KIND } from 'baseui/button';
import { Heading, HeadingLevel } from 'baseui/heading';
import { Notification, KIND as NotificationKind } from 'baseui/notification';
import { styled } from 'baseui';
import { RootState, AppDispatch } from '../../store';
import { loginWithGoogle, clearError } from '../../store/authSlice';

const Container = styled('div', {
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  height: '100vh',
  backgroundColor: '#ffffff',
});

const LoginContent = styled('div', {
  width: '400px',
  textAlign: 'center',
});

const Logo = styled('img', {
  width: '120px',
  height: '120px',
  marginBottom: '20px',
  objectFit: 'contain',
});

const GoogleSignIn: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();
  const { isAuthenticated, error } = useSelector(
    (state: RootState) => state.auth
  );

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    // Handle Google OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    
    if (code) {
      // Exchange code for token
      dispatch(loginWithGoogle({ googleToken: code }));
    }
  }, [dispatch]);

  const handleGoogleLogin = () => {
    // Redirect to Google OAuth
    const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;
    const redirectUri = `${window.location.origin}/login`;
    const scope = 'openid email profile';
    
    console.log('Google OAuth Config:', {
      clientId,
      redirectUri,
      hasClientId: !!clientId
    });
    
    if (!clientId) {
      alert('Google Client ID not configured. Please check .env file.');
      return;
    }
    
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
      `client_id=${clientId}&` +
      `redirect_uri=${encodeURIComponent(redirectUri)}&` +
      `response_type=code&` +
      `scope=${encodeURIComponent(scope)}&` +
      `access_type=offline&` +
      `prompt=consent`;
    
    console.log('Redirecting to:', authUrl);
    window.location.href = authUrl;
  };

  return (
    <Container>
      <LoginContent>
        <HeadingLevel>
          <Logo src="/greywolf_logo.png" alt="Greywolf Analytica" />
          <Heading styleLevel={3}>Greywolf Analytica</Heading>
          <div style={{ marginTop: '20px' }}>
            <Heading styleLevel={6}>
              An AI Powered Campaign Management Platform
            </Heading>
          </div>
        </HeadingLevel>
          
          <div style={{ marginTop: '40px' }}>
            <Button
              onClick={handleGoogleLogin}
              size={SIZE.large}
              kind={KIND.primary}
              overrides={{
                BaseButton: {
                  style: {
                    width: '100%',
                  },
                },
              }}
            >
              Sign in with Google
            </Button>
          </div>
          
          {error && (
            <div style={{ marginTop: '20px' }}>
              <Notification
                kind={NotificationKind.negative}
                closeable
                onClose={() => dispatch(clearError())}
              >
                {error}
              </Notification>
            </div>
          )}
          
        <div style={{ marginTop: '40px', fontSize: '12px', color: '#666' }}>
          By signing in, you agree to our Terms of Service and Privacy Policy
        </div>
      </LoginContent>
    </Container>
  );
};

export default GoogleSignIn;