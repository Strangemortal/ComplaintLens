import { configureStore } from '@reduxjs/toolkit';
import complaintsReducer from './complaintSlice';
import chatReducer from './chatSlice';

export const store = configureStore({
  reducer: {
    complaints: complaintsReducer,
    chat: chatReducer,
  },
});
