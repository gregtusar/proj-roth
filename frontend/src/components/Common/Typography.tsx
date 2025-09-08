import React from 'react';
import {
  DisplayLarge,
  DisplayMedium,
  DisplaySmall,
  DisplayXSmall,
  HeadingXXLarge,
  HeadingXLarge,
  HeadingLarge,
  HeadingMedium,
  HeadingSmall,
  HeadingXSmall,
  LabelLarge,
  LabelMedium,
  LabelSmall,
  LabelXSmall,
  ParagraphLarge,
  ParagraphMedium,
  ParagraphSmall,
  ParagraphXSmall,
  MonoDisplayLarge,
  MonoDisplayMedium,
  MonoDisplaySmall,
  MonoDisplayXSmall,
  MonoHeadingXXLarge,
  MonoHeadingXLarge,
  MonoHeadingLarge,
  MonoHeadingMedium,
  MonoHeadingSmall,
  MonoHeadingXSmall,
  MonoLabelLarge,
  MonoLabelMedium,
  MonoLabelSmall,
  MonoLabelXSmall,
  MonoParagraphLarge,
  MonoParagraphMedium,
  MonoParagraphSmall,
  MonoParagraphXSmall,
} from 'baseui/typography';

// Re-export all Base UI typography components
export {
  DisplayLarge,
  DisplayMedium,
  DisplaySmall,
  DisplayXSmall,
  HeadingXXLarge,
  HeadingXLarge,
  HeadingLarge,
  HeadingMedium,
  HeadingSmall,
  HeadingXSmall,
  LabelLarge,
  LabelMedium,
  LabelSmall,
  LabelXSmall,
  ParagraphLarge,
  ParagraphMedium,
  ParagraphSmall,
  ParagraphXSmall,
  MonoDisplayLarge,
  MonoDisplayMedium,
  MonoDisplaySmall,
  MonoDisplayXSmall,
  MonoHeadingXXLarge,
  MonoHeadingXLarge,
  MonoHeadingLarge,
  MonoHeadingMedium,
  MonoHeadingSmall,
  MonoHeadingXSmall,
  MonoLabelLarge,
  MonoLabelMedium,
  MonoLabelSmall,
  MonoLabelXSmall,
  MonoParagraphLarge,
  MonoParagraphMedium,
  MonoParagraphSmall,
  MonoParagraphXSmall,
};

// Semantic aliases for common use cases
export const PageTitle = HeadingXLarge;
export const SectionTitle = HeadingLarge;
export const CardTitle = HeadingMedium;
export const Subtitle = HeadingSmall;

export const BodyLarge = ParagraphLarge;
export const Body = ParagraphMedium;
export const BodySmall = ParagraphSmall;
export const Caption = ParagraphXSmall;

export const ButtonText = LabelMedium;
export const InputLabel = LabelMedium;
export const FieldLabel = LabelSmall;
export const Tag = LabelXSmall;

// Code/Mono variants
export const CodeBlock = MonoParagraphMedium;
export const InlineCode = MonoLabelSmall;

// Helper component for error messages
export const ErrorText: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ParagraphSmall color="negative">{children}</ParagraphSmall>
);

// Helper component for success messages
export const SuccessText: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ParagraphSmall color="positive">{children}</ParagraphSmall>
);

// Helper component for muted text
export const MutedText: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ParagraphSmall color="contentSecondary">{children}</ParagraphSmall>
);