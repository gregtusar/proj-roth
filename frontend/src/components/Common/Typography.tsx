import React from 'react';
import { styled } from 'baseui';
import {
  DisplayLarge as BaseDisplayLarge,
  DisplayMedium as BaseDisplayMedium,
  DisplaySmall as BaseDisplaySmall,
  DisplayXSmall as BaseDisplayXSmall,
  HeadingXXLarge as BaseHeadingXXLarge,
  HeadingXLarge as BaseHeadingXLarge,
  HeadingLarge as BaseHeadingLarge,
  HeadingMedium as BaseHeadingMedium,
  HeadingSmall as BaseHeadingSmall,
  HeadingXSmall as BaseHeadingXSmall,
  LabelLarge as BaseLabelLarge,
  LabelMedium as BaseLabelMedium,
  LabelSmall as BaseLabelSmall,
  LabelXSmall as BaseLabelXSmall,
  ParagraphLarge as BaseParagraphLarge,
  ParagraphMedium as BaseParagraphMedium,
  ParagraphSmall as BaseParagraphSmall,
  ParagraphXSmall as BaseParagraphXSmall,
  MonoDisplayLarge as BaseMonoDisplayLarge,
  MonoDisplayMedium as BaseMonoDisplayMedium,
  MonoDisplaySmall as BaseMonoDisplaySmall,
  MonoDisplayXSmall as BaseMonoDisplayXSmall,
  MonoHeadingXXLarge as BaseMonoHeadingXXLarge,
  MonoHeadingXLarge as BaseMonoHeadingXLarge,
  MonoHeadingLarge as BaseMonoHeadingLarge,
  MonoHeadingMedium as BaseMonoHeadingMedium,
  MonoHeadingSmall as BaseMonoHeadingSmall,
  MonoHeadingXSmall as BaseMonoHeadingXSmall,
  MonoLabelLarge as BaseMonoLabelLarge,
  MonoLabelMedium as BaseMonoLabelMedium,
  MonoLabelSmall as BaseMonoLabelSmall,
  MonoLabelXSmall as BaseMonoLabelXSmall,
  MonoParagraphLarge as BaseMonoParagraphLarge,
  MonoParagraphMedium as BaseMonoParagraphMedium,
  MonoParagraphSmall as BaseMonoParagraphSmall,
  MonoParagraphXSmall as BaseMonoParagraphXSmall,
} from 'baseui/typography';

// Font families
const INTER_FONT = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
const JETBRAINS_MONO = '"JetBrains Mono", "Fira Code", Monaco, Consolas, "Courier New", monospace';

// Wrap Base UI typography components with custom font-family
export const DisplayLarge = styled(BaseDisplayLarge, { fontFamily: INTER_FONT });
export const DisplayMedium = styled(BaseDisplayMedium, { fontFamily: INTER_FONT });
export const DisplaySmall = styled(BaseDisplaySmall, { fontFamily: INTER_FONT });
export const DisplayXSmall = styled(BaseDisplayXSmall, { fontFamily: INTER_FONT });
export const HeadingXXLarge = styled(BaseHeadingXXLarge, { fontFamily: INTER_FONT });
export const HeadingXLarge = styled(BaseHeadingXLarge, { fontFamily: INTER_FONT });
export const HeadingLarge = styled(BaseHeadingLarge, { fontFamily: INTER_FONT });
export const HeadingMedium = styled(BaseHeadingMedium, { fontFamily: INTER_FONT });
export const HeadingSmall = styled(BaseHeadingSmall, { fontFamily: INTER_FONT });
export const HeadingXSmall = styled(BaseHeadingXSmall, { fontFamily: INTER_FONT });
export const LabelLarge = styled(BaseLabelLarge, { fontFamily: INTER_FONT });
export const LabelMedium = styled(BaseLabelMedium, { fontFamily: INTER_FONT });
export const LabelSmall = styled(BaseLabelSmall, { fontFamily: INTER_FONT });
export const LabelXSmall = styled(BaseLabelXSmall, { fontFamily: INTER_FONT });
export const ParagraphLarge = styled(BaseParagraphLarge, { fontFamily: INTER_FONT });
export const ParagraphMedium = styled(BaseParagraphMedium, { fontFamily: INTER_FONT });
export const ParagraphSmall = styled(BaseParagraphSmall, { fontFamily: INTER_FONT });
export const ParagraphXSmall = styled(BaseParagraphXSmall, { fontFamily: INTER_FONT });

// Monospace variants with JetBrains Mono font
export const MonoDisplayLarge = styled(BaseMonoDisplayLarge, { fontFamily: JETBRAINS_MONO });
export const MonoDisplayMedium = styled(BaseMonoDisplayMedium, { fontFamily: JETBRAINS_MONO });
export const MonoDisplaySmall = styled(BaseMonoDisplaySmall, { fontFamily: JETBRAINS_MONO });
export const MonoDisplayXSmall = styled(BaseMonoDisplayXSmall, { fontFamily: JETBRAINS_MONO });
export const MonoHeadingXXLarge = styled(BaseMonoHeadingXXLarge, { fontFamily: JETBRAINS_MONO });
export const MonoHeadingXLarge = styled(BaseMonoHeadingXLarge, { fontFamily: JETBRAINS_MONO });
export const MonoHeadingLarge = styled(BaseMonoHeadingLarge, { fontFamily: JETBRAINS_MONO });
export const MonoHeadingMedium = styled(BaseMonoHeadingMedium, { fontFamily: JETBRAINS_MONO });
export const MonoHeadingSmall = styled(BaseMonoHeadingSmall, { fontFamily: JETBRAINS_MONO });
export const MonoHeadingXSmall = styled(BaseMonoHeadingXSmall, { fontFamily: JETBRAINS_MONO });
export const MonoLabelLarge = styled(BaseMonoLabelLarge, { fontFamily: JETBRAINS_MONO });
export const MonoLabelMedium = styled(BaseMonoLabelMedium, { fontFamily: JETBRAINS_MONO });
export const MonoLabelSmall = styled(BaseMonoLabelSmall, { fontFamily: JETBRAINS_MONO });
export const MonoLabelXSmall = styled(BaseMonoLabelXSmall, { fontFamily: JETBRAINS_MONO });
export const MonoParagraphLarge = styled(BaseMonoParagraphLarge, { fontFamily: JETBRAINS_MONO });
export const MonoParagraphMedium = styled(BaseMonoParagraphMedium, { fontFamily: JETBRAINS_MONO });
export const MonoParagraphSmall = styled(BaseMonoParagraphSmall, { fontFamily: JETBRAINS_MONO });
export const MonoParagraphXSmall = styled(BaseMonoParagraphXSmall, { fontFamily: JETBRAINS_MONO });

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