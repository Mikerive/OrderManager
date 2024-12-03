import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Alert,
} from '@mui/material';
import { useMutation, useQueryClient } from 'react-query';
import { webhookApi } from '../../api';
import { CreateWebhookRequest, WebhookEvent } from '../../types';

export const CreateWebhookForm: React.FC = () => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<CreateWebhookRequest>({
    name: '',
    url: '',
    events: [],
  });
  const [error, setError] = useState<string | null>(null);

  const createWebhookMutation = useMutation(webhookApi.createWebhook, {
    onSuccess: () => {
      queryClient.invalidateQueries('webhooks');
      // Reset form
      setFormData({
        name: '',
        url: '',
        events: [],
      });
      setError(null);
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Failed to create webhook');
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.events.length === 0) {
      setError('Please select at least one event');
      return;
    }
    createWebhookMutation.mutate(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    setError(null);
  };

  const handleEventToggle = (event: WebhookEvent) => {
    setFormData(prev => ({
      ...prev,
      events: prev.events.includes(event)
        ? prev.events.filter(e => e !== event)
        : [...prev.events, event],
    }));
    setError(null);
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Create Discord Webhook
      </Typography>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          fullWidth
          margin="normal"
          name="name"
          label="Webhook Name"
          value={formData.name}
          onChange={handleChange}
          required
        />
        <TextField
          fullWidth
          margin="normal"
          name="url"
          label="Discord Webhook URL"
          value={formData.url}
          onChange={handleChange}
          required
          placeholder="https://discord.com/api/webhooks/..."
        />
        <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
          Events
        </Typography>
        <FormGroup>
          {Object.values(WebhookEvent).map((event) => (
            <FormControlLabel
              key={event}
              control={
                <Checkbox
                  checked={formData.events.includes(event)}
                  onChange={() => handleEventToggle(event)}
                />
              }
              label={event.replace('_', ' ')}
            />
          ))}
        </FormGroup>
        <Button
          type="submit"
          variant="contained"
          fullWidth
          sx={{ mt: 3 }}
          disabled={createWebhookMutation.isLoading}
        >
          {createWebhookMutation.isLoading ? 'Creating...' : 'Create Webhook'}
        </Button>
      </Box>
    </Paper>
  );
};
