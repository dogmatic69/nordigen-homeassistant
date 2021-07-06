from . import LOGGER, CONST, DOMAIN

from nordigen_lib.sensor import build_sensors


async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform via discovery only."""
    if discovery_info is None:
        return

    LOGGER.info(
        "Nordigen will attempt to configure [%s] accounts",
        len(discovery_info["accounts"]),
    )

    entities = []
    for account in discovery_info.get("accounts"):
        LOGGER.debug("Registering sensor for account :%s", account)

        entities.extend(
            await build_sensors(
                hass=hass,
                LOGGER=LOGGER,
                account=account,
                CONST=CONST,
            )
        )

    if not len(entities):
        return False

    LOGGER.info("Total of [%s] Nordigen account sensors configured", len(entities))
    LOGGER.debug("entities :%s", entities)

    add_entities(entities)
    return True
