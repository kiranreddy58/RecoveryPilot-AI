const API_BASE = '/api/v1';

export const eventsApi = {
  createEvent: async (eventData: any) => {
    const response = await fetch(`${API_BASE}/events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(eventData),
    });
    if (!response.ok) {
      throw new Error(`Failed to create event: ${response.statusText}`);
    }
    return response.json();
  },
};
