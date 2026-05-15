import React, { useState, useRef, useEffect } from 'react';

/**
 * Tooltip component with hover trigger and smart positioning
 * @param {object} props
 * @param {React.ReactNode} props.children - Element to wrap with tooltip
 * @param {string} props.content - Tooltip content text
 * @param {number} props.delay - Hover delay in ms (default: 200)
 * @param {string} props.position - Preferred position: 'top', 'bottom', 'left', 'right' (default: 'top')
 */
function Tooltip({ children, content, delay = 200, position = 'top' }) {
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState(position);
  const timeoutRef = useRef(null);
  const triggerRef = useRef(null);
  const tooltipRef = useRef(null);

  const handleMouseEnter = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  // Adjust tooltip position if it goes off-screen
  useEffect(() => {
    if (isVisible && tooltipRef.current && triggerRef.current) {
      const tooltipRect = tooltipRef.current.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      let newPosition = position;

      // Check if tooltip goes off-screen and adjust
      if (position === 'top' && tooltipRect.top < 0) {
        newPosition = 'bottom';
      } else if (position === 'bottom' && tooltipRect.bottom > viewportHeight) {
        newPosition = 'top';
      } else if (position === 'left' && tooltipRect.left < 0) {
        newPosition = 'right';
      } else if (position === 'right' && tooltipRect.right > viewportWidth) {
        newPosition = 'left';
      }

      setTooltipPosition(newPosition);
    }
  }, [isVisible, position]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  if (!content) {
    return children;
  }

  const getTooltipStyle = () => {
    const baseStyle = {
      position: 'absolute',
      background: '#1a1a1a',
      color: '#fff',
      padding: '8px 12px',
      borderRadius: '4px',
      fontSize: '11px',
      fontWeight: 500,
      lineHeight: 1.4,
      maxWidth: '280px',
      zIndex: 1000,
      border: '1px solid rgba(255,255,255,0.15)',
      boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
      pointerEvents: 'none',
      whiteSpace: 'normal',
      wordWrap: 'break-word',
    };

    const positions = {
      top: {
        bottom: '100%',
        left: '50%',
        transform: 'translateX(-50%) translateY(-8px)',
        marginBottom: '4px',
      },
      bottom: {
        top: '100%',
        left: '50%',
        transform: 'translateX(-50%) translateY(8px)',
        marginTop: '4px',
      },
      left: {
        right: '100%',
        top: '50%',
        transform: 'translateY(-50%) translateX(-8px)',
        marginRight: '4px',
      },
      right: {
        left: '100%',
        top: '50%',
        transform: 'translateY(-50%) translateX(8px)',
        marginLeft: '4px',
      },
    };

    return { ...baseStyle, ...positions[tooltipPosition] };
  };

  const getArrowStyle = () => {
    const baseArrowStyle = {
      position: 'absolute',
      width: 0,
      height: 0,
      borderStyle: 'solid',
    };

    const arrowPositions = {
      top: {
        top: '100%',
        left: '50%',
        transform: 'translateX(-50%)',
        borderWidth: '6px 6px 0 6px',
        borderColor: '#1a1a1a transparent transparent transparent',
      },
      bottom: {
        bottom: '100%',
        left: '50%',
        transform: 'translateX(-50%)',
        borderWidth: '0 6px 6px 6px',
        borderColor: 'transparent transparent #1a1a1a transparent',
      },
      left: {
        left: '100%',
        top: '50%',
        transform: 'translateY(-50%)',
        borderWidth: '6px 0 6px 6px',
        borderColor: 'transparent transparent transparent #1a1a1a',
      },
      right: {
        right: '100%',
        top: '50%',
        transform: 'translateY(-50%)',
        borderWidth: '6px 6px 6px 0',
        borderColor: 'transparent #1a1a1a transparent transparent',
      },
    };

    return { ...baseArrowStyle, ...arrowPositions[tooltipPosition] };
  };

  return (
    <div
      ref={triggerRef}
      style={{ position: 'relative', display: 'inline-block' }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      {isVisible && (
        <div
          ref={tooltipRef}
          style={getTooltipStyle()}
          className="tooltip-fade-in"
        >
          {content}
          <div style={getArrowStyle()} />
        </div>
      )}
    </div>
  );
}

export default Tooltip;
