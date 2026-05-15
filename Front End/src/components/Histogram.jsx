import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

/**
 * Histogram Component
 * 
 * Displays score distribution using recharts BarChart with bins of width 10.
 * Requirements: 19.1, 19.2, 19.5
 */

/**
 * Bin scores into width-10 buckets
 * 
 * @param {Array} scores - Array of score values
 * @returns {Array} - Array of bin objects with range and count
 */
const binScores = (scores) => {
  // Define bins: 0-10, 11-20, 21-30, ..., 91-100, 101-105
  const bins = [
    { range: '0-10', min: 0, max: 10, count: 0 },
    { range: '11-20', min: 11, max: 20, count: 0 },
    { range: '21-30', min: 21, max: 30, count: 0 },
    { range: '31-40', min: 31, max: 40, count: 0 },
    { range: '41-50', min: 41, max: 50, count: 0 },
    { range: '51-60', min: 51, max: 60, count: 0 },
    { range: '61-70', min: 61, max: 70, count: 0 },
    { range: '71-80', min: 71, max: 80, count: 0 },
    { range: '81-90', min: 81, max: 90, count: 0 },
    { range: '91-100', min: 91, max: 100, count: 0 },
    { range: '101-105', min: 101, max: 105, count: 0 },
  ];

  // Count scores in each bin
  scores.forEach(score => {
    const bin = bins.find(b => score >= b.min && score <= b.max);
    if (bin) {
      bin.count++;
    }
  });

  return bins;
};

/**
 * Get color for bar based on score range
 */
const getBarColor = (range) => {
  const minScore = parseInt(range.split('-')[0]);
  
  if (minScore >= 81) return '#10b981'; // Green for high scores
  if (minScore >= 61) return '#3b82f6'; // Blue for good scores
  if (minScore >= 41) return '#f59e0b'; // Orange for medium scores
  return '#ef4444'; // Red for low scores
};

const Histogram = ({ scores }) => {
  if (!scores || scores.length === 0) {
    return (
      <div style={{ 
        padding: '40px', 
        textAlign: 'center', 
        color: '#6b7280',
        fontSize: '14px'
      }}>
        No score data available
      </div>
    );
  }

  // Bin the scores
  const binnedData = binScores(scores);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{
          backgroundColor: '#fff',
          border: '1px solid #d1d5db',
          borderRadius: '6px',
          padding: '12px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
        }}>
          <p style={{ margin: 0, fontWeight: 600, fontSize: '14px', color: '#1f2937' }}>
            Score Range: {data.range}
          </p>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#6b7280' }}>
            Opportunities: {data.count}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ width: '100%', height: '300px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={binnedData}
          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="range" 
            tick={{ fill: '#6b7280', fontSize: 12 }}
            label={{ 
              value: 'Score Range', 
              position: 'insideBottom', 
              offset: -10,
              style: { fill: '#374151', fontWeight: 600, fontSize: 13 }
            }}
          />
          <YAxis 
            tick={{ fill: '#6b7280', fontSize: 12 }}
            label={{ 
              value: 'Number of Opportunities', 
              angle: -90, 
              position: 'insideLeft',
              style: { fill: '#374151', fontWeight: 600, fontSize: 13 }
            }}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }} />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {binnedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.range)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default Histogram;
