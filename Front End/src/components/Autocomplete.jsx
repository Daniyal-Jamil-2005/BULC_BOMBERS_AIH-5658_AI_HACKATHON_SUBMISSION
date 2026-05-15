import React, { useState, useRef, useEffect } from 'react';
import './Autocomplete.css';

/**
 * Autocomplete Component
 * 
 * Provides autocomplete functionality for skill input with keyboard navigation.
 * Requirements: 18.1, 18.2, 18.3, 18.5
 */

// Predefined skill list (common technical and soft skills)
const PREDEFINED_SKILLS = [
  // Programming Languages
  'JavaScript', 'TypeScript', 'Python', 'Java', 'C++', 'C#', 'Go', 'Rust', 'PHP', 'Ruby', 'Swift', 'Kotlin',
  // Web Technologies
  'React', 'Angular', 'Vue.js', 'Node.js', 'Express', 'Next.js', 'HTML', 'CSS', 'Tailwind CSS', 'Bootstrap',
  // Backend & Databases
  'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'GraphQL', 'REST API', 'Microservices',
  // Cloud & DevOps
  'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'Git', 'GitHub', 'GitLab',
  // Data Science & AI
  'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Data Analysis', 'Pandas', 'NumPy', 'Scikit-learn',
  // Mobile Development
  'React Native', 'Flutter', 'iOS Development', 'Android Development', 'Mobile UI/UX',
  // Security
  'Cybersecurity', 'Network Security', 'Penetration Testing', 'Ethical Hacking', 'Cloud Security',
  // Soft Skills
  'Communication', 'Leadership', 'Team Collaboration', 'Problem Solving', 'Critical Thinking', 'Time Management',
  // Other Technical
  'Linux', 'Windows Server', 'Networking', 'System Administration', 'Agile', 'Scrum', 'Project Management'
].sort();

const Autocomplete = ({ value, onChange, placeholder = 'Type to search skills...' }) => {
  const [inputValue, setInputValue] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Filter suggestions based on input
  useEffect(() => {
    if (inputValue.trim().length > 0) {
      const filtered = PREDEFINED_SKILLS.filter(skill =>
        skill.toLowerCase().includes(inputValue.toLowerCase())
      ).slice(0, 10); // Limit to 10 suggestions
      
      setSuggestions(filtered);
      setShowSuggestions(filtered.length > 0);
      setSelectedIndex(-1);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [inputValue]);

  // Handle input change
  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  // Handle skill selection
  const handleSelectSkill = (skill) => {
    // Get current skills as array
    const currentSkills = value ? value.split(',').map(s => s.trim()).filter(s => s) : [];
    
    // Add new skill if not already present
    if (!currentSkills.includes(skill)) {
      const newSkills = [...currentSkills, skill].join(', ');
      onChange({ target: { value: newSkills } });
    }
    
    // Clear input and hide suggestions
    setInputValue('');
    setShowSuggestions(false);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  };

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!showSuggestions || suggestions.length === 0) {
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;
        
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          handleSelectSkill(suggestions[selectedIndex]);
        } else if (inputValue.trim()) {
          // Add custom skill if no suggestion selected
          handleSelectSkill(inputValue.trim());
        }
        break;
        
      case 'Escape':
        e.preventDefault();
        setShowSuggestions(false);
        setSelectedIndex(-1);
        break;
        
      default:
        break;
    }
  };

  // Scroll selected item into view
  useEffect(() => {
    if (selectedIndex >= 0 && suggestionsRef.current) {
      const selectedElement = suggestionsRef.current.children[selectedIndex];
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    }
  }, [selectedIndex]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        inputRef.current && !inputRef.current.contains(e.target) &&
        suggestionsRef.current && !suggestionsRef.current.contains(e.target)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="autocomplete-container">
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => inputValue && setShowSuggestions(suggestions.length > 0)}
        placeholder={placeholder}
        className="autocomplete-input"
        autoComplete="off"
      />
      
      {showSuggestions && suggestions.length > 0 && (
        <ul ref={suggestionsRef} className="autocomplete-suggestions show">
          {suggestions.map((skill, index) => (
            <li
              key={skill}
              className={`autocomplete-suggestion-item ${index === selectedIndex ? 'selected' : ''}`}
              onClick={() => handleSelectSkill(skill)}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              {skill}
            </li>
          ))}
        </ul>
      )}
      
      {/* Display current skills */}
      {value && (
        <div className="autocomplete-selected-skills">
          {value.split(',').map(s => s.trim()).filter(s => s).map((skill, index) => (
            <span key={index} className="skill-tag">
              {skill}
              <button
                type="button"
                onClick={() => {
                  const skills = value.split(',').map(s => s.trim()).filter(s => s);
                  skills.splice(index, 1);
                  onChange({ target: { value: skills.join(', ') } });
                }}
                className="skill-tag-remove"
                aria-label={`Remove ${skill}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default Autocomplete;
