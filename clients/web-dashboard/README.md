# Web Dashboard (not implemented in this prototype)

**Container:** Web Dashboard · **Technology:** React single-page app

The brief does not require a user interface. In the architecture, the dashboard:

- gives agronomists one view across all the client farms that have shared data with them (ASR8);
- shows only farms with an active access grant, and only the data its scopes allow (ASR9);
- gives operations staff live infrastructure load and capacity metrics, and lists devices flagged `OFFLINE` (ASR13, ASR19);
- sends every API call as JSON over HTTPS through the API Gateway, with the user's access token.
