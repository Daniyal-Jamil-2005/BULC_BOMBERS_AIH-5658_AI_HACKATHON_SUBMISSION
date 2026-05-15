import React from 'react';
import ReactWordcloud from 'react-wordcloud';

/**
 * KeywordHeatmap Component
 * 
 * Displays keyword frequency as a word cloud with frequency-based sizing.
 * Requirements: 20.3
 */

const KeywordHeatmap = ({ keywords }) => {
  if (!keywords || keywords.length === 0) {
    return (
      <div style={{ 
        padding: '40px', 
        textAlign: 'center', 
        color: '#6b7280',
        fontSize: '14px'
      }}>
        No keyword data available
      </div>
    );
  }

  // Transform keywords to format expected by react-wordcloud
  // Expected format: [{ text: 'keyword', value: frequency }, ...]
  const words = keywords.map(kw => ({
    text: kw.keyword || kw.text,
    value: kw.frequency || kw.value || 1
  }));

  // Word cloud options
  const options = {
    colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'],
    enableTooltip: true,
    deterministic: true,
    fontFamily: 'Inter, sans-serif',
    fontSizes: [14, 60],
    fontStyle: 'normal',
    fontWeight: 'bold',
    padding: 2,
    rotations: 2,
    rotationAngles: [0, 90],
    scale: 'sqrt',
    spiral: 'archimedean',
    transitionDuration: 1000
  };

  return (
    <div style={{ width: '100%', height: '300px' }}>
      <ReactWordcloud 
        words={words} 
        options={options}
      />
    </div>
  );
};

export default KeywordHeatmap;
