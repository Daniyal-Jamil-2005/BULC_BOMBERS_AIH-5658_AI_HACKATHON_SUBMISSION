import API_CONFIG from '../config';

/**
 * Save user profile to backend
 * @param {string} userId - User identifier
 * @param {object} profile - Profile data
 * @returns {Promise<object>} Response from server
 */
export async function saveProfile(userId, profile) {
  const response = await fetch(`${API_CONFIG.baseURL}/profile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      profile: {
        degree: profile.degree,
        semester: Number(profile.semester),
        cgpa: Number(profile.cgpa),
        skills: typeof profile.skills === 'string' 
          ? profile.skills.split(',').map(s => s.trim()).filter(Boolean)
          : profile.skills,
        preferred_opportunity_types: typeof profile.types === 'string'
          ? profile.types.split(',').map(s => s.trim()).filter(Boolean)
          : profile.preferred_opportunity_types || [],
        location_preference: profile.location || profile.location_preference,
        financial_need: profile.financial === 'true' || profile.financial === true,
        total_semesters: Number(profile.totalSemesters || profile.total_semesters || 8),
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to save profile: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Load user profile from backend
 * @param {string} userId - User identifier
 * @returns {Promise<object|null>} Profile data or null if not found
 */
export async function loadProfile(userId) {
  const response = await fetch(`${API_CONFIG.baseURL}/profile/${userId}`);

  if (!response.ok) {
    throw new Error(`Failed to load profile: ${response.statusText}`);
  }

  const data = await response.json();
  
  if (data.status === 'not_found' || !data.profile) {
    return null;
  }

  // Convert backend format to frontend format
  return {
    degree: data.profile.degree,
    semester: data.profile.semester,
    cgpa: data.profile.cgpa,
    location: data.profile.location_preference,
    skills: data.profile.skills.join(', '),
    types: data.profile.preferred_opportunity_types.join(', '),
    experience: '',
    financial: data.profile.financial_need,
    totalSemesters: data.profile.total_semesters,
  };
}

/**
 * Get or create user ID from localStorage
 * @returns {string} User ID
 */
export function getUserId() {
  let userId = localStorage.getItem('inbox_copilot_user_id');
  
  if (!userId) {
    // Generate a simple UUID-like ID
    userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('inbox_copilot_user_id', userId);
  }
  
  return userId;
}
