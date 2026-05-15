import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import './AnalyticsDashboard.css';
import Histogram from './Histogram';
import KeywordHeatmap from './KeywordHeatmap';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

function AnalyticsDashboard({ analytics }) {
  if (!analytics) {
    return null;
  }

  const { descriptive_stats, type_distribution, urgency_distribution, opportunities, keywords } = analytics;

  // Extract scores for histogram
  const scores = opportunities ? opportunities.map(opp => opp.final_score || 0) : [];

  // Prepare data for type distribution chart
  const typeData = Object.entries(type_distribution || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value
  }));

  // Prepare data for urgency distribution chart
  const urgencyData = Object.entries(urgency_distribution || {}).map(([name, value]) => ({
    name,
    value
  }));

  return (
    <div className="analytics-dashboard">
      <h2>📊 Analytics Dashboard</h2>
      
      {/* Descriptive Statistics */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Mean Score</div>
          <div className="stat-value">{descriptive_stats?.mean?.toFixed(1) || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Std Deviation</div>
          <div className="stat-value">{descriptive_stats?.std?.toFixed(1) || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Median (50th)</div>
          <div className="stat-value">{descriptive_stats?.percentiles?.['50']?.toFixed(1) || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">90th Percentile</div>
          <div className="stat-value">{descriptive_stats?.percentiles?.['90']?.toFixed(1) || 0}</div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Type Distribution */}
        {typeData.length > 0 && (
          <div className="chart-card">
            <h3>Opportunity Types</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={typeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {typeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Urgency Distribution */}
        {urgencyData.length > 0 && (
          <div className="chart-card">
            <h3>Urgency Distribution</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={urgencyData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Score Distribution Histogram */}
        {scores.length > 0 && (
          <div className="chart-card">
            <h3>Score Distribution</h3>
            <Histogram scores={scores} />
          </div>
        )}

        {/* Keyword Heatmap */}
        {keywords && keywords.length > 0 && (
          <div className="chart-card">
            <h3>Keyword Frequency</h3>
            <KeywordHeatmap keywords={keywords} />
          </div>
        )}
      </div>
    </div>
  );
}

export default AnalyticsDashboard;
