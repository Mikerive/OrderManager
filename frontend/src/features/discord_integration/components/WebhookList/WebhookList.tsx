import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Typography,
  Box,
  Chip,
  Switch,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Send as SendIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { webhookApi } from '../../api';
import { WebhookConfig, WebhookEvent } from '../../types';

export const WebhookList: React.FC = () => {
  const queryClient = useQueryClient();
  const { data: webhooks, isLoading, error } = useQuery('webhooks', webhookApi.getWebhooks);

  const toggleWebhookMutation = useMutation(
    ({ id, is_active }: { id: number; is_active: boolean }) =>
      webhookApi.updateWebhook(id, { is_active }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('webhooks');
      },
    }
  );

  const deleteWebhookMutation = useMutation(webhookApi.deleteWebhook, {
    onSuccess: () => {
      queryClient.invalidateQueries('webhooks');
    },
  });

  const testWebhookMutation = useMutation(webhookApi.testWebhook);

  const handleToggleActive = async (webhook: WebhookConfig) => {
    try {
      await toggleWebhookMutation.mutateAsync({
        id: webhook.id,
        is_active: !webhook.is_active,
      });
    } catch (error) {
      console.error('Failed to toggle webhook:', error);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteWebhookMutation.mutateAsync(id);
    } catch (error) {
      console.error('Failed to delete webhook:', error);
    }
  };

  const handleTest = async (id: number) => {
    try {
      await testWebhookMutation.mutateAsync(id);
    } catch (error) {
      console.error('Failed to test webhook:', error);
    }
  };

  if (isLoading) return <Typography>Loading webhooks...</Typography>;
  if (error) return <Typography color="error">Error loading webhooks</Typography>;

  return (
    <Box sx={{ width: '100%', overflowX: 'auto' }}>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>URL</TableCell>
              <TableCell>Events</TableCell>
              <TableCell>Active</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {webhooks?.map((webhook: WebhookConfig) => (
              <TableRow key={webhook.id}>
                <TableCell>{webhook.name}</TableCell>
                <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {webhook.url}
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {webhook.events.map((event: WebhookEvent) => (
                      <Chip
                        key={event}
                        label={event.replace('_', ' ')}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </TableCell>
                <TableCell>
                  <Switch
                    checked={webhook.is_active}
                    onChange={() => handleToggleActive(webhook)}
                  />
                </TableCell>
                <TableCell>
                  <IconButton
                    onClick={() => handleTest(webhook.id)}
                    title="Test Webhook"
                  >
                    <SendIcon />
                  </IconButton>
                  <IconButton
                    onClick={() => handleDelete(webhook.id)}
                    title="Delete Webhook"
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};
