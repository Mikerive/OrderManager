import React from 'react';
import { useQuery } from 'react-query';
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
} from '@mui/material';
import { Cancel as CancelIcon } from '@mui/icons-material';
import { ordersApi, Order } from '../api/orders';

export const OrderList: React.FC = () => {
  const { data: orders, isLoading, error } = useQuery('orders', ordersApi.getOrders);

  const handleCancelOrder = async (orderId: number) => {
    try {
      await ordersApi.cancelOrder(orderId);
      // Refetch orders after cancellation
      // You might want to use react-query's mutation here instead
    } catch (error) {
      console.error('Failed to cancel order:', error);
    }
  };

  if (isLoading) return <Typography>Loading orders...</Typography>;
  if (error) return <Typography color="error">Error loading orders</Typography>;

  return (
    <Box sx={{ width: '100%', overflowX: 'auto' }}>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Symbol</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Side</TableCell>
              <TableCell>Quantity</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {orders?.map((order: Order) => (
              <TableRow key={order.id}>
                <TableCell>{order.id}</TableCell>
                <TableCell>{order.title}</TableCell>
                <TableCell>{order.symbol}</TableCell>
                <TableCell>{order.order_type}</TableCell>
                <TableCell>{order.side}</TableCell>
                <TableCell>{order.quantity}</TableCell>
                <TableCell>{order.status}</TableCell>
                <TableCell>
                  <IconButton
                    onClick={() => handleCancelOrder(order.id)}
                    disabled={order.status !== 'active'}
                  >
                    <CancelIcon />
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
