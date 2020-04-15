import argparse
import time

import requests
import logging

from requests import codes


class KifliClient:
    TIME_SLOT_URL = "/timeslots-api/0"

    def __init__(self, url="https://www.kifli.hu/services/frontend-service") -> None:
        self._url = url

    def get_free_slots(self, address_id: int):
        free_slots = []
        res = requests.get(self._url + KifliClient.TIME_SLOT_URL, params={"userId": "", "addressId": address_id})
        if res.status_code != codes.ok:
            logging.error(f"Error requesting slots: {res.content}")
        else:
            availability_days = res.json()["data"]["availabilityDays"]
            for day in availability_days:
                for slot in map(lambda x: x[0], day['slots'].values()):
                    if slot["timeSlotCapacityDTO"]["totalFreeCapacityPercent"]:
                        since, till = slot["since"], slot["till"]
                        free_slots.append(f"{since} - {till}")
        return free_slots


def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser("Kifli.hu notification sender on free delivery slot")
    parser.add_argument("--address_id", "-a", type=int, required=True, help="Address id")
    parser.add_argument("--email", "-e", type=str, required=True, help="Email recipment")
    parser.add_argument("--mailgun_api_key", "-m", type=str, required=True, help="Mailgun api key")
    parser.add_argument("--mailgun_domain", "-d", type=str, required=True, help="Mailgun domain")
    parser.add_argument("--frequency", "-f", type=int, default=60, help="Query frequency")

    args = parser.parse_args()
    k = KifliClient()

    while True:
        try:
            slots = k.get_free_slots(args.address_id)
            if slots:
                logging.info(f"Free slots found: {slots}")
                logging.info(f"Sending mail to {args.email}")
                res = requests.post(
                    f"https://api.eu.mailgun.net/v3/{args.mailgun_domain}/messages",
                    auth=("api", args.mailgun_api_key),
                    data={
                        "from": f"KifliBot <info@{args.mailgun_domain}>",
                        "to": ["User", args.email],
                        "subject": "Kifli -- Elérhető időpont!",
                        "text": "\n".join(slots)
                    }
                )
                if res.status_code != codes.ok:
                    logging.error(f"Error calling mailgun: {res.content}")
                break
            else:
                logging.info(f"No free slots, next query in {args.frequency} secs")
                time.sleep(args.frequency)
        except KeyboardInterrupt:
            break
    logging.info("Exiting")


if __name__ == "__main__":
    main()
