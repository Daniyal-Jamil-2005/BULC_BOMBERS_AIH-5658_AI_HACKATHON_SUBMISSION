import React from 'react';
import './SkillGapAnalysis.css';

/**
 * SkillGapAnalysis Component
 * 
 * Displays missing skills identified from opportunity analysis with frequency bars.
 * Shows which skills appear most frequently in opportunities but are missing from
 * the student's profile.
 * 
 * Requirements: 4.5
 */
function SkillGapAnalysis({ skillGaps }) {
  if (!skillGaps || skillGaps.length === 0) {
    return (
      <div className="skill-gap-analysis">
        <h3>📊 Skill Gap Analysis</h3>
        <p className="no-gaps">Great! No significant skill gaps identified.</p>
      </div>
    );
  }

  // Find max frequency for scaling bars
  const maxFrequency = Math.max(...skillGaps.map(gap => gap.frequency));

  // Categorize skills by demand level
  const getSkillDemandLevel = (frequency) => {
    const percentage = (frequency / maxFrequency) * 100;
    if (percentage >= 70) return 'high';
    if (percentage >= 40) return 'medium';
    return 'low';
  };

  return (
    <div className="skill-gap-analysis">
      <h3>📊 Skill Gap Analysis</h3>
      <p className="description">
        Skills that appear frequently in opportunities but are missing from your profile:
      </p>
      
      <div className="skill-gaps-list">
        {skillGaps.map((gap, index) => {
          const demandLevel = getSkillDemandLevel(gap.frequency);
          const barWidth = (gap.frequency / maxFrequency) * 100;
          
          return (
            <div key={index} className="skill-gap-item">
              <div className="skill-header">
                <span className="skill-name">{gap.skill}</span>
                <span className={`demand-badge ${demandLevel}`}>
                  {demandLevel === 'high' && '🔥 High Demand'}
                  {demandLevel === 'medium' && '⚡ Medium Demand'}
                  {demandLevel === 'low' && '💡 Low Demand'}
                </span>
                <span className="frequency-count">{gap.frequency} opportunities</span>
              </div>
              <div className="frequency-bar-container">
                <div 
                  className={`frequency-bar ${demandLevel}`}
                  style={{ width: `${barWidth}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="skill-gap-footer">
        <p className="tip">
          💡 <strong>Tip:</strong> Consider learning high-demand skills to increase your match rate for future opportunities.
        </p>
      </div>
    </div>
  );
}

export default SkillGapAnalysis;
