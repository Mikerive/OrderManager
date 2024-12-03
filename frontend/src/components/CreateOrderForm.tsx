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
} from '@mui/material';
import { CreateOrderRequest, ordersApi } from '../api/orders';

const orderTypes = ['market', 'limit', 'stop', 'stop_limit'];
const orderSides = ['buy', 'sell'];
const providers = ['alpaca']; // Add more providers as needed

export const CreateOrderForm: React.FC = () => {
  const [formData, setFormData] = React.useState<CreateOrderRequest>({
    title: '',
    symbol: '',
    quantity: 0,
    order_type: 'market',
    side: 'buy',
    provider: 'alpaca',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await ordersApi.createOrder(formData);
      // Reset form or show success message
    } catch (error) {
      console.error('Failed to create order:', error);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name as string]: value,
    }));
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
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
              {orderTypes.map(type => (
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
              {orderSides.map(side => (
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
              {providers.map(provider => (
                <MenuItem key={provider} value={provider}>
                  {provider.toUpperCase()}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        {formData.order_type !== 'market' && (
          <Grid item xs={12}>
            <TextField
              fullWidth
              name="price"
              label="Price"
              type="number"
              value={formData.price || ''}
              onChange={handleChange}
              required
            />
          </Grid>
        )}
        <Grid item xs={12}>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
          >
            Create Order
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
};
