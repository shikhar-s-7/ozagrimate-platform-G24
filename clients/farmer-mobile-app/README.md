# Farmer Mobile App (not implemented in this prototype)

**Container:** Farmer Mobile App · **Technology:** React Native

The brief does not require a user interface. In the architecture, the app:

- shows a farmer their latest readings, alerts and irrigation advice, refreshed at least every 15 minutes (ASR1);
- caches the last data it received, so it stays usable on patchy rural coverage;
- receives alerts as push notifications through the Push Notification Service; critical alerts also arrive by SMS when push fails (ASR6);
- lets the farmer grant and revoke an agronomist's access to their farm's data (endpoints #7–8);
- sends every API call as JSON over HTTPS through the API Gateway, with the farmer's access token;
- links out to the Agricultural Marketplace.
