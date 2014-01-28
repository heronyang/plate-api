class Urls(object):
    EMPTY_PLATE_IMAGE_URL = "http://static.plate.tw/plate_empty.png"

class Configs(object):
    MAX_TOTAL_PRICE_PER_ORDER = 3000
    MAX_ACCEPTABLE_FAILURE = 2
    PRIOR_NUMBER_SLIPS = 3
    MINUTES_LOCK_BETWEEN_REGISTRATIONS = 0

    # Normally only allow one oustanding order per customer
    # Turn on only for testing
    ALLOW_MULTIPLE_OUTSTANDING_ORDERS = True
