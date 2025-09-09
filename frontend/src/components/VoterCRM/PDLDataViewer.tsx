import React, { useState } from 'react';
import { styled } from 'baseui';
import { ChevronRight, ChevronDown } from 'baseui/icon';
import { Tag } from 'baseui/tag';
import { LabelSmall, ParagraphSmall } from 'baseui/typography';

const Container = styled('div', ({ $theme }) => ({
  backgroundColor: $theme.colors.backgroundSecondary,
  borderRadius: $theme.borders.radius400,
  padding: $theme.sizing.scale600,
  maxHeight: '600px',
  overflow: 'auto',
  fontSize: '14px',
  fontFamily: $theme.typography.font450.fontFamily,
}));

const Row = styled<'div', { $indent?: number }>('div', ({ $theme, $indent = 0 }) => ({
  paddingLeft: `${$indent * 20}px`,
  marginBottom: $theme.sizing.scale200,
  display: 'flex',
  alignItems: 'flex-start',
  flexWrap: 'wrap',
  gap: $theme.sizing.scale200,
}));

const Key = styled('span', ({ $theme }) => ({
  fontWeight: 600,
  color: $theme.colors.contentPrimary,
  marginRight: $theme.sizing.scale200,
  minWidth: '150px',
  textTransform: 'capitalize',
}));

const Value = styled('span', ({ $theme }) => ({
  color: $theme.colors.contentSecondary,
  flex: 1,
  wordBreak: 'break-word',
}));

const ToggleButton = styled('button', ({ $theme }) => ({
  background: 'none',
  border: 'none',
  padding: 0,
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  color: $theme.colors.contentTertiary,
  ':hover': {
    color: $theme.colors.contentPrimary,
  },
}));

const ArrayContainer = styled('div', ({ $theme }) => ({
  marginTop: $theme.sizing.scale200,
  paddingLeft: $theme.sizing.scale600,
  borderLeft: `2px solid ${$theme.colors.borderOpaque}`,
}));

const ObjectContainer = styled('div', ({ $theme }) => ({
  marginTop: $theme.sizing.scale200,
  padding: $theme.sizing.scale400,
  backgroundColor: $theme.colors.backgroundPrimary,
  borderRadius: $theme.borders.radius200,
  border: `1px solid ${$theme.colors.borderOpaque}`,
}));

const EmptyState = styled('div', ({ $theme }) => ({
  color: $theme.colors.contentTertiary,
  fontStyle: 'italic',
  padding: $theme.sizing.scale600,
  textAlign: 'center',
}));

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({ 
  title, 
  children, 
  defaultOpen = false 
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  
  return (
    <div>
      <ToggleButton onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
        <Key style={{ marginLeft: '8px', minWidth: 'auto' }}>{title}</Key>
      </ToggleButton>
      {isOpen && <div style={{ marginTop: '8px' }}>{children}</div>}
    </div>
  );
};

interface PDLDataViewerProps {
  data: any;
  indent?: number;
}

const formatKey = (key: string): string => {
  // Convert snake_case to Title Case
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

const getValueType = (value: any): string => {
  if (value === null) return 'null';
  if (Array.isArray(value)) return 'array';
  return typeof value;
};

const renderValue = (value: any, key: string = ''): React.ReactNode => {
  const type = getValueType(value);
  
  switch (type) {
    case 'null':
      return <Tag kind="neutral" closeable={false}>null</Tag>;
    
    case 'boolean':
      return (
        <Tag 
          kind={value ? "positive" : "negative"} 
          closeable={false}
        >
          {value ? 'true' : 'false'}
        </Tag>
      );
    
    case 'number':
      return <Tag kind="primary" closeable={false}>{value}</Tag>;
    
    case 'string':
      // Special formatting for certain fields
      if (key.includes('date') || key.includes('year')) {
        return <Tag kind="accent" closeable={false}>{value}</Tag>;
      }
      if (key.includes('email')) {
        return (
          <a href={`mailto:${value}`} style={{ color: '#0066cc' }}>
            {value}
          </a>
        );
      }
      if (key.includes('phone')) {
        return (
          <a href={`tel:${value}`} style={{ color: '#0066cc' }}>
            {value}
          </a>
        );
      }
      if (key.includes('url') || key.includes('link')) {
        return (
          <a 
            href={value} 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ color: '#0066cc' }}
          >
            {value}
          </a>
        );
      }
      return <Value>{value}</Value>;
    
    default:
      return null;
  }
};

const PDLDataViewer: React.FC<PDLDataViewerProps> = ({ data, indent = 0 }) => {
  if (!data) {
    return <EmptyState>No PDL data available</EmptyState>;
  }

  const type = getValueType(data);
  
  if (type === 'array') {
    if (data.length === 0) {
      return <EmptyState>Empty array</EmptyState>;
    }
    
    return (
      <ArrayContainer>
        {data.map((item: any, index: number) => (
          <div key={index} style={{ marginBottom: '12px' }}>
            <LabelSmall>[{index}]</LabelSmall>
            <PDLDataViewer data={item} indent={indent + 1} />
          </div>
        ))}
      </ArrayContainer>
    );
  }
  
  if (type === 'object') {
    const entries = Object.entries(data);
    
    if (entries.length === 0) {
      return <EmptyState>Empty object</EmptyState>;
    }
    
    // Group entries by type for better organization
    const simpleEntries = entries.filter(([_, value]) => {
      const vType = getValueType(value);
      return vType !== 'object' && vType !== 'array';
    });
    
    const complexEntries = entries.filter(([_, value]) => {
      const vType = getValueType(value);
      return vType === 'object' || vType === 'array';
    });
    
    return (
      <div>
        {/* Render simple values first */}
        {simpleEntries.map(([key, value]) => (
          <Row key={key} $indent={indent}>
            <Key>{formatKey(key)}:</Key>
            {renderValue(value, key)}
          </Row>
        ))}
        
        {/* Render complex values in collapsible sections */}
        {complexEntries.map(([key, value]) => {
          const vType = getValueType(value);
          const itemCount = vType === 'array' ? 
            ` (${(value as any[]).length} items)` : 
            vType === 'object' ? ` (${Object.keys(value as object).length} fields)` : '';
          
          return (
            <Row key={key} $indent={indent}>
              <CollapsibleSection 
                title={`${formatKey(key)}${itemCount}`}
                defaultOpen={key === 'emails' || key === 'phones'}
              >
                {vType === 'object' ? (
                  <ObjectContainer>
                    <PDLDataViewer data={value} indent={0} />
                  </ObjectContainer>
                ) : (
                  <PDLDataViewer data={value} indent={indent + 1} />
                )}
              </CollapsibleSection>
            </Row>
          );
        })}
      </div>
    );
  }
  
  // For primitive values
  return <div>{renderValue(data)}</div>;
};

export default PDLDataViewer;