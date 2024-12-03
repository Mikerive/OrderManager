import React from 'react';
import {
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Typography,
  Paper,
} from '@mui/material';
import { useMutation, useQueryClient } from 'react-query';
import { ordersApi } from '../../api';
import { CreateOrderRequest, OrderType, OrderSide } from '../../types';

const PROVIDERS = ['alpaca'] as const;

export const CreateOrderForm: React.FC = () => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = React.useState<CreateOrderRequest>({
    title: '',
    symbol: '',
    quantity: 0,
    order_type: OrderType.MARKET,
    side: OrderSide.BUY,
    provider: PROVIDERS[0],
  });

  const createOrderMutation = useMutation(ordersApi.createOrder, {
    onSuccess: () => {
      queryClient.invalidateQueries('orders');
      // Reset form
      setFormData({
        title: '',
        symbol: '',
        quantity: 0,
        order_type: OrderType.MARKET,
        side: OrderSide.BUY,
        provider: PROVIDERS[0],
      });
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    createOrderMutation.mutate(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name as string]: value,
    }));
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Box component="form" onSubmit={handleSubmit}>
        <Typography variant="h6" gutterBottom>
          Create New Order
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              name="title"
              label="Order Title"
              value={formData.title}
              onChange={handleChange}
              required
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              name="symbol"
              label="Symbol"
              value={formData.symbol}
              onChange={handleChange}
              required
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              name="quantity"
              label="Quantity"
              type="number"
              value={formData.quantity}
              onChange={handleChange}
              required
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth>
              <InputLabel>Order Type</InputLabel>
              <Select
                name="order_type"
                value={formData.order_type}
                label="Order Type"
                onChange={handleChange}
              >
                {Object.values(OrderType).map(type => (
                  <MenuItem key={type} value={type}>
                    {type.toUpperCase()}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth>
              <InputLabel>Side</InputLabel>
              <Select
                name="side"
                value={formData.side}
                label="Side"
                onChange={handleChange}
              >
                {Object.values(OrderSide).map(side => (
                  <MenuItem key={side} value={side}>
                    {side.toUpperCase()}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth>
              <InputLabel>Provider</InputLabel>
              <Select
                name="provider"
                value={formData.provider}
                label="Provider"
                onChange={handleChange}
              >
                {PROVIDERS.map(provider => (
                  <MenuItem key={provider} value={provider}>
                    {provider.toUpperCase()}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          {formData.order_type !== OrderType.MARKET && (
            <>
              {(formData.order_type === OrderType.LIMIT || formData.order_type === OrderType.STOP_LIMIT) && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    name="limit_price"
                    label="Limit Price"
                    type="number"
                    value={formData.limit_price || ''}
                    onChange={handleChange}
                    required
                  />
                </Grid>
              )}
              {(formData.order_type === OrderType.STOP || formData.order_type === OrderType.STOP_LIMIT) && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    name="stop_price"
                    label="Stop Price"
                    type="number"
                    value={formData.stop_price || ''}
                    onChange={handleChange}
                    required
                  />
                </Grid>
              )}
            </>
          )}
          <Grid item xs={12}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              fullWidth
              disabled={createOrderMutation.isLoading}
            >
              {createOrderMutation.isLoading ? 'Creating...' : 'Create Order'}
            </Button>
          </Grid>
        </Grid>
      </Box>
    </Paper>
  );
};
