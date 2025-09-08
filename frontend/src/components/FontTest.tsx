import React from 'react';
import { styled } from 'baseui';
import {
  HeadingXLarge,
  HeadingLarge,
  HeadingMedium,
  ParagraphLarge,
  ParagraphMedium,
  LabelMedium,
  MonoParagraphMedium,
} from './Common/Typography';

const Container = styled('div', ({ $theme }) => ({
  padding: $theme.sizing.scale800,
  display: 'flex',
  flexDirection: 'column',
  gap: $theme.sizing.scale600,
  backgroundColor: $theme.colors.backgroundPrimary,
}));

const FontTest: React.FC = () => {
  return (
    <Container>
      <HeadingXLarge>HeadingXLarge - Should be Inter 700</HeadingXLarge>
      <HeadingLarge>HeadingLarge - Should be Inter 600</HeadingLarge>
      <HeadingMedium>HeadingMedium - Should be Inter 600</HeadingMedium>
      <ParagraphLarge>ParagraphLarge - Should be Inter 400</ParagraphLarge>
      <ParagraphMedium>ParagraphMedium - Should be Inter 400</ParagraphMedium>
      <LabelMedium>LabelMedium - Should be Inter 500</LabelMedium>
      <MonoParagraphMedium>MonoParagraphMedium - Should be JetBrains Mono</MonoParagraphMedium>
      
      <div style={{ marginTop: '20px' }}>
        <h3 style={{ fontFamily: 'Inter' }}>Direct Inter Font Test</h3>
        <p style={{ fontFamily: 'JetBrains Mono' }}>Direct JetBrains Mono Test</p>
      </div>
      
      <div style={{ marginTop: '20px' }}>
        <h3>Current computed font-family:</h3>
        <p id="computed-font">Will be shown here...</p>
      </div>
    </Container>
  );
};

export default FontTest;