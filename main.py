import os
import requests
import json
import pandas as pd
from datetime import datetime

#os.environ["http_proxy"] = "http://localhost:8000"
#os.environ["https_proxy"] = "https://localhost:8000"

USERNAME = ""
PASSWORD = ""
CUSTOMER_ID = ""

class NTTAHandler:

    def __init__(self, username, password):
        """
        """
        self.username = username
        self.password = password
        self.session  = requests.session() 

    def login(self):
        """
        """
        headers = {
                "Accept":"application/json, text/plain, */*",
                "Accept-Encoding":"gzip, deflate, br",
                "Accept-Language":"en-US,en;q=0.9,zh-US;q=0.8,zh;q=0.7,tr;q=0.6",
                "Content-Type":"application/json",
                "Origin":"https://ssptrips.ntta.org",
                "Referer":"https://ssptrips.ntta.org/",
                "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0"
            }

        payload = {
                    "UserName":self.username,
                    "Password":self.password,
                    "Grant_Type":"password",
                    "IsZipcashCustomer":True,
                    "RememberMe":False
                }
        r = self.session.post(
                "https://sptrips.ntta.org/CustomerPortal/api/authenticate",
                headers=headers,
                data=json.dumps(payload),
                verify=False
                )

        r.raise_for_status()

        data = r.json()

        self.auth = data["access_token"]

    def fetch_statement(self, id: str, ) -> str:
        """
        """
        headers = {
                "Accept":"application/json, text/plain, */*",
                "Accept-Encoding":"gzip, deflate, br",
                "Accept-Language":"en-US,en;q=0.9,zh-US;q=0.8,zh;q=0.7,tr;q=0.6",
                "Content-Type":"application/json",
                "Origin":"https://ssptrips.ntta.org",
                "Referer":"https://ssptrips.ntta.org/",
                "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0",
                "Authorization":f"Bearer {self.auth}",
                "Api-Origin":"CustomerPortal"

            }

        payload = {
          "Paging": {
            "PageNumber": 0,
            "PageSize": 50,
            "SortDir": 1,
            "SortColumn": "POSTEDDATE"
          },
          "StartDate": "6/01/2023, 12:00:00 AM",
          "EndDate": "9/18/2023, 11:59:59 PM",
          "TrnsTypes": "",
          "Transponder": "",
          "Plates": "",
          "customerId": id,
          "TransactionDateType": "false",
          "ExportAs": "XLSX",
          "IsViolator": True,
          "AppCurrDate": datetime.now().strftime("%m/%d/%Y %I:%H:%M %p") 
        }
        r = self.session.post(
                f"https://sptrips.ntta.org/CustomerPortal/api/customers/{id}/transhistory",
                headers=headers,
                data=json.dumps(payload),
                verify=False)
        r.raise_for_status()

        return r.content

    def fetch_transaction_info(self,account_id: str,
                                    transaction_id:str) -> list:
        """
        """
        headers = {
                    "Accept":"application/json, text/plain, */*",
                    "Accept-Encoding":"gzip, deflate, br",
                    "Accept-Language":"en-US,en;q=0.9,zh-US;q=0.8,zh;q=0.7,tr;q=0.6",
                    "Content-Type":"application/json",
                    "Origin":"https://ssptrips.ntta.org",
                    "Referer":"https://ssptrips.ntta.org/",
                    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0",
                    "Authorization":f"Bearer {self.auth}",
                    "Api-Origin":"CustomerPortal"

                }

        r = requests.get(
                ("https://sptrips.ntta.org/CustomerPortal/api/"
                f"customers/{account_id}/tripsadjustment/{transaction_id}/false"),
                headers=headers,
                verify=False
                )
        r.raise_for_status()
        data = r.json()
        
        return [
                data["VehicleNumber"],
                data["VehicleState"],
                ]
    def append_vehicle_info(self,account_id:str,
                            statement: pd.DataFrame) -> pd.DataFrame:
        """
        """
        statement[["License Plate#", "License State"]] = statement\
                .apply(lambda row:
                    self.fetch_transaction_info(account_id,row["Transaction ID"])
                       if row["Transaction Type"] == "TOLL" else ["",""],
                       axis=1,
                       result_type="expand")

        return statement

if __name__ == "__main__":

    handler = NTTAHandler(USERNAME,PASSWORD)
    handler.login()
    df = pd.read_excel(handler.fetch_statement(CUSTOMER_ID))
    handler.append_vehicle_info(CUSTOMER_ID, df)

    df.to_excel("ntta_statement.xlsx", index=False)


