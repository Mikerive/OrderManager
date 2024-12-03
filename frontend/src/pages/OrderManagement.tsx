import React from 'react';
import { Container, Paper, Box, Tab, Tabs } from '@mui/material';
import { OrderList } from '../components/OrderList';
import { CreateOrderForm } from '../components/CreateOrderForm';

export const OrderManagement: React.FC = () => {
  const [tabValue, setTabValue] = React.useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Paper sx={{ p: 2 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Orders List" />
            <Tab label="Create Order" />
          </Tabs>
        </Box>
        
        {tabValue === 0 && <OrderList />}
        {tabValue === 1 && <CreateOrderForm />}
      </Paper>
    </Container>
  );
};
