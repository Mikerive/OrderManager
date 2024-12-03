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
  Chip,
} from '@mui/material';
import {
  Cancel as CancelIcon,
  Delete as DeleteIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { ordersApi } from '../../api';
import { Order, OrderStatus } from '../../types';
import { OrderStatusChip } from '../OrderStatusChip';

export const OrderList: React.FC = () => {
  const { data: orders, isLoading, error, refetch } = useQuery('orders', ordersApi.getOrders);

  const handleCancelOrder = async (orderId: number) => {
    try {
      await ordersApi.cancelOrder(orderId);
      refetch();
    } catch (error) {
      console.error('Failed to cancel order:', error);
    }
  };

  const handleDeleteOrder = async (orderId: number) => {
    try {
      await ordersApi.deleteOrder(orderId);
      refetch();
    } catch (error) {
      console.error('Failed to delete order:', error);
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
              <TableCell>Provider</TableCell>
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
                <TableCell>
                  <OrderStatusChip status={order.status} />
                </TableCell>
                <TableCell>{order.provider}</TableCell>
                <TableCell>
                  <IconButton
                    onClick={() => handleCancelOrder(order.id)}
                    disabled={order.status !== OrderStatus.ACTIVE}
                    title="Cancel Order"
                  >
                    <CancelIcon />
                  </IconButton>
                  <IconButton
                    onClick={() => handleDeleteOrder(order.id)}
                    disabled={order.status === OrderStatus.ACTIVE}
                    title="Delete Order"
                  >
                    <DeleteIcon />
                  </IconButton>
                  <IconButton
                    // TODO: Implement order details view
                    onClick={() => {}}
                    title="View Details"
                  >
                    <InfoIcon />
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
