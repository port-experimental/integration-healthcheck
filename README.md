# integration-healthcheck

An integration providing healthcheck capabilities and visualization to Port integrations within Port

![image](https://github.com/user-attachments/assets/7862a0ce-0add-4f08-acc8-c4d4627e72a2)

## Installation
To install the integration, you should have the following:
- A Port account and [your Port credentials](https://docs.port.io/build-your-software-catalog/custom-integration/api/#find-your-port-credentials)
- Python 3.12+
- Poetry. If you don't have it, install it with `pip install poetry`

## Setup
1. Clone the repository
2. Run `poetry install` to install the dependencies
3. Copy the `.env.example` file to `.env` and fill in the missing values
4. Run `make run` to run the integration


## Known issues
- The integration itself running is not yet able to detect its own health since it is still in execution, so you might see inaccurate health statuses for the integration itself.
- There may be discrepancies between the status of the integration and the health of the integration. This is because the status of the integration is based on the last resync, while the health is based on several factors including audit logs errors, integration log errors and the presence of a resync state