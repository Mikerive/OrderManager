import React from 'react';
import { Container, Paper, Box, Tab, Tabs, Typography } from '@mui/material';
import { WebhookList } from '../components/WebhookList/WebhookList';
import { CreateWebhookForm } from '../components/CreateWebhookForm/CreateWebhookForm';

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
      id={`discord-tabpanel-${index}`}
      aria-labelledby={`discord-tab-${index}`}
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

export const DiscordIntegrationPage: React.FC = () => {
  const [tabValue, setTabValue] = React.useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Discord Integration
      </Typography>
      <Paper sx={{ width: '100%', mb: 2 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="discord integration tabs"
          >
            <Tab label="Webhooks" id="discord-tab-0" />
            <Tab label="Create Webhook" id="discord-tab-1" />
          </Tabs>
        </Box>
        <TabPanel value={tabValue} index={0}>
          <WebhookList />
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          <CreateWebhookForm />
        </TabPanel>
      </Paper>
    </Container>
  );
};
