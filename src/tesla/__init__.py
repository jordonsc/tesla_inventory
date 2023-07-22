import json
import urllib.parse
import requests
import os
import logging
import traceback
from boto3 import Session


class Inventory:
    API_URL = "https://www.tesla.com/inventory/api/v1/inventory-results?query="

    def __init__(self, market: str, region: str):
        self.market = market
        self.region = region

    def fetch(self, model: str, trim=None, condition: str = "new") -> dict:
        """
        Run a query against the Tesla inventory API to get latest available stock.
        """
        query = {
            "query": {
                "model": model.lower(),
                "condition": condition.lower(),
                "options": {
                    "FleetSalesRegions": [
                        self.region
                    ],
                },
                "arrangeby": "Relevance",
                "order": "desc",
                "market": self.market,
                "language": "en",
                "super_region": "north america",
            },
            "offset": 0,
            "count": 50,
            "outsideOffset": 0,
            "outsideSearch": False
        }

        if trim is not None:
            query["query"]["options"]["TRIM"] = trim

        url = self.API_URL + urllib.parse.quote(json.dumps(query))

        logging.info("Getting latest inventory..")
        logging.debug(f"GET {url}")

        r = requests.get(url).json()
        logging.info(f"{r['total_matches_found']} vehicles listed")

        return r


class Notifier:
    MATCH_ON = "Hash"

    def __init__(self, cache_file: str, arn: str):
        self.cache_file = cache_file
        self.arn = arn

        self.session = Session(profile_name="tesla")
        self.sns = self.session.client("sns")

        self.msg_dispatch = []

        if os.path.isfile(cache_file):
            with open(cache_file, "r") as fp:
                self.cache = json.load(fp)
        else:
            self.cache = {"results": [], "total_matches_found": 0}
            logging.warning("Cache file does not exist")

    def process_results(self, results: dict):
        """
        Parse the provided results and alert on new vehicles not found in the cache.
        """
        try:
            if int(results['total_matches_found']) > 0:
                for vehicle in results['results']:
                    if not self.is_cached(vehicle):
                        self.process_vehicle(vehicle)

                self.dispatch()

            self.update_cache(results)
        except Exception as e:
            logging.error(f"Error '{type(e)}' parsing results\n" + traceback.format_exc())
            self.update_cache(results, error_log=True)
            self.clean_cache()

    def process_vehicle(self, v: dict):
        """
        Creates messages for new vehicle listings.

        These are stored, not dispatched. When all vehicles are processed, dispatch the messages in one with dispatch().
        """
        title = f"{v['Year']} {v['TrimName']}"
        if v['IsDemo']:
            title += " (demo)"

        paint = ", ".join(v['PAINT']) + " / " + ", ".join(v['INTERIOR']).replace("PREMIUM_", "")
        msg = f"{title}\n{paint}, {v['Odometer']} {v['OdometerTypeShort']}, ${v['Price']}"

        logging.info(f"{msg}")
        self.msg_dispatch.append(msg)

    def dispatch(self):
        """
        Send an SNS alert for new vehicles.

        Will do nothing if no vehicles were prepared with process_vehicle(). Clears vehicle pool after dispatching.
        """
        if len(self.msg_dispatch) == 0:
            return

        payload = "New vehicles listed:\n\n" + "\n---\n".join(self.msg_dispatch)

        logging.debug("Sending SNS alert")
        self.sns.publish(
            TargetArn=self.arn,
            Message=json.dumps({'default': payload}),
            MessageStructure='json',
            MessageAttributes={},
        )

        self.msg_dispatch = []

    def is_cached(self, v: dict) -> bool:
        """
        Check if a vehicle is present in the cached data.
        """
        for vehicle in self.cache['results']:
            if vehicle[self.MATCH_ON] == v[self.MATCH_ON]:
                return True

        return False

    def update_cache(self, results: dict, error_log: bool = False):
        """
        Writes the latest (provided) results to the cache file.
        """
        error_fn = self.cache_file + ".err"

        with open(error_fn if error_log else self.cache_file, "w") as fp:
            fp.write(json.dumps(results))

        if not error_log and os.path.isfile(error_fn):
            try:
                os.unlink(error_fn)
            except Exception as e:
                logging.error(f"Error '{type(e)}' removing previous error result dump\n" + traceback.format_exc())

    def clean_cache(self):
        """
        Writes a blank cache file, useful if the cache is corrupted.
        """
        with open(self.cache_file, "w") as fp:
            fp.write(json.dumps({"results": [], "total_matches_found": 0}))
