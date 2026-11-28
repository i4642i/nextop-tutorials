"""Price and time of a visit from the salon's menu (salon.json: every service has styles with a price and minutes)."""
from functions._salon import menu, quote, salon, style_index, style_names

NAME = "price_quote"
DESC = ("Price and duration from the salon's menu. styles: the menu names the customer chose, one per service (they "
        "add up): the result has each style's price and minutes and the total. services alone (cut, perm, color, "
        "treatment): the menu of those services with every style's price and minutes, for a customer who asks what there "
        "is or what it costs before choosing. Tell the customer the prices exactly as returned.")
GROUP = "salon"
SCHEMA = {
    "type": "object",
    "properties": {
        "styles": {"type": "array", "minItems": 1, "uniqueItems": True,
                   "items": {"type": "string", "enum": style_names()}},
        "services": {"type": "array", "minItems": 1, "uniqueItems": True,
                     "items": {"type": "string", "enum": list(salon()["services"])}},
    },
}


def run(ctx, args):
    if args.get("styles"):
        index = style_index()
        services = [index[n][0] for n in args["styles"]]
        if len(set(services)) < len(services):
            return {"error": "give one style per service"}
        return quote(args["styles"])
    if args.get("services"):
        return {"menu": menu(args["services"])}
    return {"error": "give styles (the chosen menu names) or services (to see their menu)"}
