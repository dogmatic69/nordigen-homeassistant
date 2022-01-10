from nordigen import wrapper as Client
import requests


def get_client(**kwargs):
    return Client(**kwargs)


def get_reference(enduser_id, institution_id, *args, **kwargs):
    return f"{enduser_id}-{institution_id}"


def unique_ref(id, account):
    for key in ["iban", "bban", "resourceId"]:
        val = account.get(key)
        if val:
            return val
    return id


def get_requisitions(client, configs, logger, const):
    requisitions = []
    try:
        requisitions = client.requisitions.list()["results"]
    except (requests.exceptions.HTTPError, KeyError) as error:
        logger.error("Unable to fetch Nordigen requisitions: %s", error)

    processed = []
    for config in configs:
        processed.append(
            get_or_create_requisition(
                fn_create=client.requisitions.create,
                fn_remove=client.requisitions.remove,
                fn_info=client.requisitions.by_id,
                requisitions=requisitions,
                reference=get_reference(**config),
                institution_id=config[const["INSTITUTION_ID"]],
                logger=logger,
                config=config,
            )
        )

    return processed


def get_or_create_requisition(fn_create, fn_remove, fn_info, requisitions, reference, institution_id, logger, config):
    requisition = matched_requisition(reference, requisitions)
    if requisition and requisition.get("status") in ["EX", "SU"]:
        fn_remove(
            **{
                "id": requisition["id"],
            }
        )

        logger.info("Requisition was in failed state, removed :%s", requisition)
        requisition = None

    if not requisition:
        requisition = fn_create(
            **{
                "redirect": "https://127.0.0.1/",
                "institution_id": institution_id,
                "reference": reference,
            }
        )
        logger.debug("No requisition found, created :%s", requisition)

    if requisition.get("status") != "LN":
        logger.debug("Requisition not linked :%s", requisition)
        logger.info("Authenticate and accept connection and restart :%s", requisition["link"])

    if not requisition.get("details"):
        requisition["details"] = {
            "id": "N26_NTSBDEB1",
            "name": "N26 Bank",
            "bic": "NTSBDEB1",
            "transaction_total_days": "730",
            "countries": ["SI"],
            "logo": "https://cdn.nordigen.com/ais/N26_NTSBDEB1.png",
        }
        del requisition["details"]["countries"]

    requisition["config"] = config
    return requisition


def get_accounts(fn, requisition, logger, ignored):
    accounts = []
    for account_id in requisition.get("accounts", []):
        if account_id in ignored:
            logger.info("Account ignored due to configuration :%s", account_id)
            continue

        accounts.append(
            get_account(
                fn=fn,
                id=account_id,
                requisition=requisition,
                logger=logger,
            )
        )
    return [account for account in accounts if account]


def get_account(fn, id, requisition, logger):
    account = {}
    try:
        account = fn(id)
        account = account.get("account", {})
    except Exception as error:
        logger.error("Unable to fetch account details from Nordigen: %s", error)
        return

    if not account.get("iban"):
        logger.warn("No iban: %s | %s", requisition, account)

    ref = unique_ref(id, account)

    account = {
        "id": id,
        "unique_ref": ref,
        "name": account.get("name"),
        "owner": account.get("ownerName"),
        "currency": account.get("currency"),
        "product": account.get("product"),
        "status": account.get("status"),
        "bic": account.get("bic"),
        "iban": account.get("iban"),
        "bban": account.get("bban"),
    }
    logger.info("Loaded account info for account # :%s", id)
    return account


def matched_requisition(ref, requisitions):
    for requisition in requisitions:
        if requisition["reference"] == ref:
            return requisition

    return {}
