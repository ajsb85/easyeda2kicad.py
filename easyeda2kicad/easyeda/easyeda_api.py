# Global imports
import logging
from typing import Optional
import requests

from easyeda2kicad import __version__

API_ENDPOINT = "https://easyeda.com/api/products/{lcsc_id}/components?version=6.4.19.5"
LCSC_PRICES_API_ENDPOINT = "https://easyeda.com/api/getPrices?numbers={lcsc_id}&version=6.5.47"
JLCPCB_STOCK_API_ENDPOINT = "https://easyeda.com/api/components/getSmtPartInfo?version=6.5.47&numbers={lcsc_id}"
ENDPOINT_3D_MODEL = "https://modules.easyeda.com/3dmodel/{uuid}"
ENDPOINT_3D_MODEL_STEP = "https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/{uuid}"
# ENDPOINT_3D_MODEL_STEP found in https://modules.lceda.cn/smt-gl-engine/0.8.22.6032922c/smt-gl-engine.js : points to the bucket containing the step files.

# ------------------------------------------------------------


class EasyedaApi:
    def __init__(self) -> None:
        self.headers = {
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": f"easyeda2kicad v{__version__}",
        }

    def get_info_from_easyeda_api(self, lcsc_id: str) -> dict:
        r = requests.get(url=API_ENDPOINT.format(lcsc_id=lcsc_id), headers=self.headers)
        api_response = r.json()

        if not api_response or (
            "code" in api_response and api_response["success"] is False
        ):
            logging.debug(f"{api_response}")
            return {}

        return r.json()

    def get_cad_data_of_component(self, lcsc_id: str) -> dict:
        cp_cad_info = self.get_info_from_easyeda_api(lcsc_id=lcsc_id)
        if cp_cad_info == {}:
            return {}
        result = cp_cad_info["result"]

        # Add the current lcsc price
        lcsc_price = self.get_lcsc_price(lcsc_id=lcsc_id)
        if lcsc_price:
            result["lcsc_price"] = lcsc_price

        # Add the current jlcpcb stock
        stock_num = self.get_jlcpcb_stock(lcsc_id=lcsc_id)
        if stock_num:
            result["jlc_stock"] = stock_num        

        return result
    
    def get_lcsc_price(self, lcsc_id: str) -> Optional[float]:
        r = requests.get(url=LCSC_PRICES_API_ENDPOINT.format(lcsc_id=lcsc_id), headers=self.headers)
        api_response = r.json()

        if not api_response or (
            api_response.get("success", False) is False
        ):
            logging.debug(f"{api_response}")
            return None

        results = api_response.get("result", [])
        for result in results:
            price = result.get("lcsc", {}).get("price")
            if price:
                return price
        logging.warning(f"No price available for {lcsc_id} on LCSC")
        return None

    def get_jlcpcb_stock(self, lcsc_id: str) -> Optional[int]:
        r = requests.get(url=JLCPCB_STOCK_API_ENDPOINT.format(lcsc_id=lcsc_id), headers=self.headers)
        api_response = r.json()

        if not api_response or (
            api_response.get("success", False) is False
        ):
            logging.debug(f"{api_response}")
            return None

        result = api_response.get("result", {})
        stock = result.get("stock_num", None)
        if stock == None:
            logging.debug(f"No SMT service available for {lcsc_id}")
        return stock

    def get_raw_3d_model_obj(self, uuid: str) -> str:
        r = requests.get(
            url=ENDPOINT_3D_MODEL.format(uuid=uuid),
            headers={"User-Agent": self.headers["User-Agent"]},
        )
        if r.status_code != requests.codes.ok:
            logging.error(f"No raw 3D model data found for uuid:{uuid} on easyeda")
            return None
        return r.content.decode()

    def get_step_3d_model(self, uuid: str) -> bytes:
        r = requests.get(
            url=ENDPOINT_3D_MODEL_STEP.format(uuid=uuid),
            headers={"User-Agent": self.headers["User-Agent"]},
        )
        if r.status_code != requests.codes.ok:
            logging.error(f"No step 3D model data found for uuid:{uuid} on easyeda")
            return None
        return r.content
