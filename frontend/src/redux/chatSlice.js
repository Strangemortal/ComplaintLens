import { createSlice } from '@reduxjs/toolkit';

const initialWelcomeMessage = {
  role: 'assistant',
  content: 'Hello, I am your QMS AI Co-Pilot. I will help you log product complaints and perform automated QA risk assessments. Describe the complaint in natural language, or drag & drop a PDF report into the chat to begin.',
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
};

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [initialWelcomeMessage],
  },
  reducers: {
    addMessage: (state, action) => {
      const { role, content, is_mock } = action.payload;
      state.messages.push({
        role,
        content,
        is_mock: is_mock || false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      });
    },
    clearChat: (state) => {
      state.messages = [initialWelcomeMessage];
    },
  },
});

export const { addMessage, clearChat } = chatSlice.actions;
export default chatSlice.reducer;
