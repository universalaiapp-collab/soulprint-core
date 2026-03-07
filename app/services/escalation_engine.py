def should_escalate(payload):

    action = payload.get("action")

    if action == "transfer":
        amount = payload.get("amount", 0)

        if amount > 50000:
            return True

    return False
