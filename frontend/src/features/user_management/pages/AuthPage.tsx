import React, { useState } from 'react';
import { Container, Paper, Tabs, Tab, Box } from '@mui/material';
import { LoginForm } from '../components/LoginForm/LoginForm';
import { RegisterForm } from '../components/RegisterForm/RegisterForm';

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
      id={`auth-tabpanel-${index}`}
      aria-labelledby={`auth-tab-${index}`}
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

export const AuthPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="sm">
      <Paper sx={{ mt: 8 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="auth tabs"
            centered
          >
            <Tab label="Login" id="auth-tab-0" />
            <Tab label="Register" id="auth-tab-1" />
          </Tabs>
        </Box>
        <TabPanel value={tabValue} index={0}>
          <LoginForm />
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          <RegisterForm />
        </TabPanel>
      </Paper>
    </Container>
  );
};
