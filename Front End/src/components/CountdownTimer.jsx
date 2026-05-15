import React, { useState, useEffect } from 'react';
import './CountdownTimer.css';

/**
 * CountdownTimer Component
 * 
 * Displays a live countdown timer showing days, hours, and minutes remaining until a deadline.
 * Updates every minute and applies visual warnings for urgent deadlines.
 * 
 * Requirements: 16.1, 16.2, 16.5
 */
const CountdownTimer = ({ deadlineIso, urgencyBadge }) => {
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    if (!deadlineIso) {
      setTimeRemaining(null);
      return;
    }

    // Calculate time remaining
    const calculateTimeRemaining = () => {
      const now = new Date();
      const deadline = new Date(deadlineIso);
      const diff = deadline - now;

      if (diff <= 0) {
        setIsExpired(true);
        setTimeRemaining(null);
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

      setTimeRemaining({ days, hours, minutes, totalHours: diff / (1000 * 60 * 60) });
      setIsExpired(false);
    };

    // Initial calculation
    calculateTimeRemaining();

    // Update every minute
    const interval = setInterval(calculateTimeRemaining, 60000);

    return () => clearInterval(interval);
  }, [deadlineIso]);

  if (!deadlineIso) {
    return null;
  }

  if (isExpired) {
    return (
      <div className="countdown-timer expired">
        <span className="countdown-label">EXPIRED</span>
      </div>
    );
  }

  if (!timeRemaining) {
    return null;
  }

  // Determine if deadline is urgent (< 24 hours)
  const isUrgent = timeRemaining.totalHours < 24;

  return (
    <div className={`countdown-timer ${isUrgent ? 'urgent' : ''}`}>
      <div className="countdown-segments">
        {timeRemaining.days > 0 && (
          <div className="countdown-segment">
            <span className="countdown-value">{timeRemaining.days}</span>
            <span className="countdown-unit">{timeRemaining.days === 1 ? 'day' : 'days'}</span>
          </div>
        )}
        <div className="countdown-segment">
          <span className="countdown-value">{timeRemaining.hours}</span>
          <span className="countdown-unit">{timeRemaining.hours === 1 ? 'hr' : 'hrs'}</span>
        </div>
        <div className="countdown-segment">
          <span className="countdown-value">{timeRemaining.minutes}</span>
          <span className="countdown-unit">{timeRemaining.minutes === 1 ? 'min' : 'mins'}</span>
        </div>
      </div>
      {isUrgent && (
        <div className="countdown-warning">
          <span className="warning-icon">⚠️</span>
          <span className="warning-text">Urgent</span>
        </div>
      )}
    </div>
  );
};

export default CountdownTimer;
