# integration-healthcheck

An integration providing healthcheck capabilities and visualization to Port integrations within Port

![image](https://github.com/user-attachments/assets/7862a0ce-0add-4f08-acc8-c4d4627e72a2)

## Installation
To install the integration, you should have the following:
- A Port account and [your Port credentials](https://docs.port.io/build-your-software-catalog/custom-integration/api/#find-your-port-credentials)
- Docker installed on your machine

## Setup
Run the Docker image with the following command:

```
docker run --name integration-healthcheck -e OCEAN__PORT__CLIENT_ID=<your-client-id> -e OCEAN__PORT__CLIENT_SECRET=<your-client-secret> -e OCEAN__PORT__BASE_URL=https://api.getport.io -e OCEAN__EVENT_LISTENER__TYPE=POLLING ghcr.io/port-experimental/integration-healthcheck
```

## Known issues
- The integration itself running is not yet able to detect its own health since it is still in execution, so you might see inaccurate health statuses for the integration itself.
- There may be discrepancies between the status of the integration and the health of the integration. This is because the status of the integration is based on the last resync, while the health is based on several factors including audit logs errors, integration log errors and the presence of a resync state.