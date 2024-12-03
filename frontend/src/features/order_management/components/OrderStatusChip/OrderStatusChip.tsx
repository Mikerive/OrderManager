import React from 'react';
import { Chip } from '@mui/material';
import { OrderStatus } from '../../types';

interface OrderStatusChipProps {
  status: OrderStatus;
}

const statusColors = {
  [OrderStatus.PENDING]: 'warning',
  [OrderStatus.ACTIVE]: 'info',
  [OrderStatus.FILLED]: 'success',
  [OrderStatus.CANCELLED]: 'error',
  [OrderStatus.FAILED]: 'error',
} as const;

export const OrderStatusChip: React.FC<OrderStatusChipProps> = ({ status }) => {
  return (
    <Chip
      label={status.toUpperCase()}
      color={statusColors[status]}
      size="small"
    />
  );
};
