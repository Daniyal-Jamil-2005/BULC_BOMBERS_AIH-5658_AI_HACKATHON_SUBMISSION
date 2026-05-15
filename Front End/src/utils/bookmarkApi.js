import API_CONFIG from '../config';
import { getUserId } from './profileApi';

/**
 * Save an opportunity as a bookmark
 * @param {object} opportunity - Opportunity data to bookmark
 * @returns {Promise<object>} Response from server
 */
export async function addBookmark(opportunity) {
  const userId = getUserId();
  
  const response = await fetch(`${API_CONFIG.baseURL}/bookmarks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      opportunity_id: opportunity.id.toString(),
      opportunity_data: opportunity,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to add bookmark: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Remove a bookmark
 * @param {string} opportunityId - ID of the opportunity to unbookmark
 * @returns {Promise<object>} Response from server
 */
export async function removeBookmark(opportunityId) {
  const userId = getUserId();
  
  const response = await fetch(`${API_CONFIG.baseURL}/bookmarks/${userId}/${opportunityId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Failed to remove bookmark: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get all bookmarked opportunities
 * @returns {Promise<Array>} List of bookmarked opportunities
 */
export async function getBookmarks() {
  const userId = getUserId();
  
  const response = await fetch(`${API_CONFIG.baseURL}/bookmarks/${userId}`);

  if (!response.ok) {
    throw new Error(`Failed to get bookmarks: ${response.statusText}`);
  }

  const data = await response.json();
  return data.bookmarks || [];
}

/**
 * Check if an opportunity is bookmarked
 * @param {string} opportunityId - ID of the opportunity
 * @param {Array} bookmarks - List of bookmarked opportunities
 * @returns {boolean} True if bookmarked
 */
export function isBookmarked(opportunityId, bookmarks) {
  return bookmarks.some(b => b.opportunity_id === opportunityId.toString());
}
