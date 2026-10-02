import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

const API_BASE = 'http://localhost:8000/api';

const initialFormState = {
  product_name: '',
  strength: '',
  batch_number: '',
  manufacturing_date: '',
  expiry_date: '',
  quantity: '',
  complaint_description: '',
};

const initialRiskState = {
  severity: '',
  priority: '',
  reason: '',
  impact: '',
  recommended_action: '',
};

// Async Thunks
export const fetchComplaintsList = createAsyncThunk(
  'complaints/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE}/complaints`);
      if (!response.ok) {
        let errMsg = 'Failed to fetch historical complaints.';
        try {
          const errData = await response.json();
          if (errData?.detail) errMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
        } catch (_) {}
        throw new Error(errMsg);
      }
      return await response.json();
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const saveComplaintToDb = createAsyncThunk(
  'complaints/save',
  async ({ form, risk }, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE}/complaints`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ form, risk }),
      });
      if (!response.ok) {
        let errMsg = 'Failed to save complaint to database.';
        try {
          const errData = await response.json();
          if (errData?.detail) errMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
        } catch (_) {}
        throw new Error(errMsg);
      }
      return await response.json();
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const deleteComplaintFromDb = createAsyncThunk(
  'complaints/delete',
  async (id, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE}/complaints/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        let errMsg = 'Failed to delete complaint record.';
        try {
          const errData = await response.json();
          if (errData?.detail) errMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
        } catch (_) {}
        throw new Error(errMsg);
      }
      return id;
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);


export const uploadComplaintPDF = createAsyncThunk(
  'complaints/uploadPDF',
  async (file, { rejectWithValue, dispatch }) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process PDF.');
      }
      
      const data = await response.json();
      
      // Also add AI response to the chat log
      dispatch({
        type: 'chat/addMessage',
        payload: { role: 'assistant', content: data.chat_response },
      });
      
      return data;
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

// We define the chat integration here so it can write directly to activeComplaint / activeRisk
export const sendChatMessage = createAsyncThunk(
  'complaints/sendChat',
  async (messageText, { getState, rejectWithValue, dispatch }) => {
    try {
      const state = getState();
      const current_form = state.complaints.activeComplaint;
      const current_risk = state.complaints.activeRisk;

      // Add user message to chat log
      dispatch({
        type: 'chat/addMessage',
        payload: { role: 'user', content: messageText },
      });

      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageText,
          current_form,
          current_risk,
        }),
      });

      if (!response.ok) {
        let errMsg = 'API failed to respond.';
        try {
          const errData = await response.json();
          if (errData?.detail) errMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
        } catch (_) {}
        throw new Error(errMsg);
      }
      const data = await response.json();

      // Add AI response to chat log
      dispatch({
        type: 'chat/addMessage',
        payload: { role: 'assistant', content: data.chat_response, is_mock: data.is_mock },
      });

      return data;
    } catch (err) {
      // Add error feedback in chat
      dispatch({
        type: 'chat/addMessage',
        payload: { role: 'assistant', content: `❌ Error: ${err.message}. Ensure your backend server is running on port 8000.` },
      });
      return rejectWithValue(err.message);
    }
  }
);

const complaintsSlice = createSlice({
  name: 'complaints',
  initialState: {
    activeComplaint: initialFormState,
    activeRisk: initialRiskState,
    complaintsList: [],
    loading: false,
    saveSuccess: false,
    error: null,
  },
  reducers: {
    clearActiveComplaint: (state) => {
      state.activeComplaint = initialFormState;
      state.activeRisk = initialRiskState;
      state.saveSuccess = false;
    },
    resetSaveSuccess: (state) => {
      state.saveSuccess = false;
    },
    updateFormField: (state, action) => {
      const { field, value } = action.payload;
      state.activeComplaint[field] = value;
    },
    loadComplaintRecord: (state, action) => {
      const c = action.payload;
      state.activeComplaint = {
        product_name: c.product_name || '',
        strength: c.strength || '',
        batch_number: c.batch_number || '',
        manufacturing_date: c.manufacturing_date || '',
        expiry_date: c.expiry_date || '',
        quantity: c.quantity || '',
        complaint_description: c.complaint_description || '',
      };
      if (c.risk_assessment) {
        state.activeRisk = {
          severity: c.risk_assessment.severity || '',
          priority: c.risk_assessment.priority || '',
          reason: c.risk_assessment.reason || '',
          impact: c.risk_assessment.impact || '',
          recommended_action: c.risk_assessment.recommended_action || '',
        };
      }
    }
  },

  extraReducers: (builder) => {
    builder
      // Fetch list
      .addCase(fetchComplaintsList.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchComplaintsList.fulfilled, (state, action) => {
        state.loading = false;
        state.complaintsList = action.payload;
      })
      .addCase(fetchComplaintsList.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Save complaint
      .addCase(saveComplaintToDb.pending, (state) => {
        state.loading = true;
        state.saveSuccess = false;
      })
      .addCase(saveComplaintToDb.fulfilled, (state, action) => {
        state.loading = false;
        state.saveSuccess = true;
        state.complaintsList.unshift(action.payload); // Add to dashboard list
        state.activeComplaint = initialFormState;
        state.activeRisk = initialRiskState;
      })
      .addCase(saveComplaintToDb.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
        state.saveSuccess = false;
      })
      // Delete complaint
      .addCase(deleteComplaintFromDb.fulfilled, (state, action) => {
        state.complaintsList = state.complaintsList.filter((c) => c.id !== action.payload);
      })
      // Upload PDF
      .addCase(uploadComplaintPDF.pending, (state) => {
        state.loading = true;
      })
      .addCase(uploadComplaintPDF.fulfilled, (state, action) => {
        state.loading = false;
        state.activeComplaint = action.payload.form;
        state.activeRisk = action.payload.risk;
      })
      .addCase(uploadComplaintPDF.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Send Chat Message
      .addCase(sendChatMessage.pending, (state) => {
        state.loading = true;
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.loading = false;
        // Update current complaint form and risk state
        if (action.payload.form) state.activeComplaint = action.payload.form;
        if (action.payload.risk) state.activeRisk = action.payload.risk;
      })
      .addCase(sendChatMessage.rejected, (state) => {
        state.loading = false;
      });
  },
});

export const { 
  clearActiveComplaint, 
  resetSaveSuccess, 
  updateFormField, 
  loadComplaintRecord 
} = complaintsSlice.actions;
export default complaintsSlice.reducer;


