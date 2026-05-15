import API_CONFIG from '../config';
import { getUserId } from './profileApi';

/**
 * Save checklist item state
 * @param {string} opportunityId - ID of the opportunity
 * @param {string} task - Task description
 * @param {boolean} done - Completion status
 * @returns {Promise<object>} Response from server
 */
export async function saveChecklistItem(opportunityId, task, done) {
  const userId = getUserId();
  
  const response = await fetch(`${API_CONFIG.baseURL}/checklists`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      opportunity_id: opportunityId.toString(),
      task: task,
      done: done,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to save checklist item: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get checklist for an opportunity
 * @param {string} opportunityId - ID of the opportunity
 * @returns {Promise<Array>} List of checklist items
 */
export async function getChecklist(opportunityId) {
  const userId = getUserId();
  
  const response = await fetch(`${API_CONFIG.baseURL}/checklists/${userId}/${opportunityId}`);

  if (!response.ok) {
    throw new Error(`Failed to get checklist: ${response.statusText}`);
  }

  const data = await response.json();
  return data.checklist || [];
}
