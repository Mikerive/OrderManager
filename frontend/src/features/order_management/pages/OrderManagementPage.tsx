import React from 'react';
import { Container, Paper, Box, Tab, Tabs, Typography } from '@mui/material';
import { OrderList } from '../components/OrderList/OrderList';
import { CreateOrderForm } from '../components/CreateOrderForm/CreateOrderForm';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`order-tabpanel-${index}`}
      aria-labelledby={`order-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export const OrderManagementPage: React.FC = () => {
  const [tabValue, setTabValue] = React.useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Order Management
      </Typography>
      <Paper sx={{ width: '100%', mb: 2 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="order management tabs"
          >
            <Tab label="Orders List" id="order-tab-0" />
            <Tab label="Create Order" id="order-tab-1" />
          </Tabs>
        </Box>
        <TabPanel value={tabValue} index={0}>
          <OrderList />
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          <CreateOrderForm />
        </TabPanel>
      </Paper>
    </Container>
  );
};
