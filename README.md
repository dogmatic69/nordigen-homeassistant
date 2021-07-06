# Nordigen Home Assistant integration

This integration will allow you to have access to banking data for most banks
in the EU.

![](/pics/sensor-examle.png)

## Installation

HACS coming soon!

You will need to register on Nordigen and get an API key before you can run this
integration. At this time there is only support for one API key per HA instance.

1. Copy / clone this integration into `./config/custom_components/nordigen`
1. Restart Home Assistant
1. Add your config to `./config/configuration.yaml` or similar
1. Validate the config using UI or CLI.
1. Restart Home Assistant
1. Monitor logs for the authentication URL. Copy URL to your browser and follow directions for authenticating and approving the connection.
1. Restart Home Assistant once again after authenticating to the bank
1. Your sensors should now be available.

In the future I hope to be able to make the system a bit more dynamic and user
friendly for account onboarding :)

## Configuration

| Name              | Type    | Requirement     | Description                                          |
| ----------------- | ------- | ------------    | -------------------------------------------          |
| token             | string  | **Required**    | Your secret API token from Nordigen (use `!secret`!) |
| requisitions      | array   | **Required**    | List of banking institutions that will be connected  |
| debug             | boolean | **Optional**    | Still connects to the bank for account name, but balance is randomly generated witout connecting to the bank. (default `False`)  |

This integration pairs a "user id" with a banking institution. Each banking
institution will return one or more accounts, each of which can have multiple
types of balances.

Each requisition can contain the following options:

| Name                | Type    | Requirement     | Description                                          |
| ------------------- | ------- | ------------    | -------------------------------------------          |
| enduser_id          | string  | **Required**    | A unique (to your HA install) identifier for the user these accounts will belong to. Generally a UUID |
| aspsp_id            | string  | **Required**    | The bank code for the institution being connected. This can be found either in the API examples on Nordigen or using the Client Libs (there are hundreds)  |
| refresh_rate        | integer | **Optional**    | Time in minutes between refresh (default is `240` min / 4 hours). Some banks are limited to 4 requests / day  |
| ignore_accounts     | array   | **Optional**    | List of account numbers to ignore. For example might add accounts for 2 partners including a joint account (which would show up twice, once for each user).   |
| available_balance   | boolean | **Optional**    | Create a sensor based on the available balance (default `True`) |
| booked_balance      | boolean | **Optional**    | Create a sensor based on the booked balance (pending transactions) (default `True`)  |
| max_historical_days | integer | **Optional**    | Maximum days of history to collect (default `30`) |
| icon                | string  | **Optional**    | Icon to use for the sensor, defaults to the currency symbol or USD when not available as an icon (default `mdi:currency-usd-circle`) |

### Example Config

Assuming you bank with a single institution, your config may look like this.

```yaml
nordigen:
  token: !secret nordigen
  requisitions:
    - enduser_id: user-id-1
      aspsp_id: BANK_A
```

Should you have more than one institution you use (credit cards are often apart from current acounts)

```yaml
nordigen:
  token: !secret nordigen
  requisitions:
    - enduser_id: user-id-1
      aspsp_id: BANK_A
    - enduser_id: user-id-1
      aspsp_id: BANK_B
```

Multiple users with the same institution, but ignoring an account

```yaml
nordigen:
  token: !secret nordigen
  requisitions:
    - enduser_id: user-id-1
      aspsp_id: BANK_A
    - enduser_id: user-id-2
      aspsp_id: BANK_A
      ignore_accounts:
        - ACCOUNT_ID_1234
```

### Derivative Sensors

You can build derivative sensors to view your total wealth for example

```yaml
sensor:
  - platform: template
    sensors:
      my_wealth:
        unit_of_measurement: SEK
        value_template: |
          {{
            (
              (states('sensor.account_123_available') | float) +
              (states('sensor.account_456_available') | float) +
              (states('sensor.account_789_available') | float) +
            ) | round(2)
          }}
```

### Automations

Turn off your outside lights when your account balance is getting low.

```yaml
automation:
  - alias: "broke"
    trigger:
      - platform: numeric_state
          entity_id: sensor.account_123_available
          below: 2500
    action:
    - service: light.turn_off
        target:
        entity_id: light.exterior_lighting
```

## Technical details

I wanted to have good test coverage and could not find a good way to do it within
this integration so I've abstracted out all the code into a [standalone python lib].

That in turn uses a generic API [clinet lib] for Nordigen

## About Nordigen

[Nordigen] is an all-in-one banking data API for building powerful banking, lending
and finance apps. They offer a free API for fetching account info, balances and
transactions. They also handle all the authentication between the banks and do
a little bit of data nomilisation.

Check out the [Nordigen API] for full details.



[standalone python lib]: https://pypi.org/project/nordigen-ha-lib/
[client lib]: https://pypi.org/project/nordigen-python/

[Nordigen]: https://nordigen.com/
[Nordigen API]: https://nordigen.com/en/account_information_documenation/api-documention/overview/


