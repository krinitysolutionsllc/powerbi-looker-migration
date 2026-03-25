import os

from dotenv import load_dotenv

from lib.power_bi_client import PowerBIAppClient
from pprint import pprint

load_dotenv()

# from lib.power_bi_client import PowerBIUserClient
# with PowerBIUserClient(
#     os.environ["AZURE_CLIENT_ID"],
#     os.environ["AZURE_TENANT_ID"],
# ) as pbi:
#     r = pbi.call("get", "reports")
#     r.raise_for_status()
#     print(r.json())

with PowerBIAppClient(
    os.environ["393a8cbe-7126-46dc-95e8-5068f76540bf"],
    os.environ["21616937-0c44-4144-9f56-09145c4cabb3"],
    os.environ["AZURE_SECRET_VALUE"],
) as pbi:
    r = pbi.call("get", "https://api.powerbi.com/v1.0/myorg/groups/f956fa46-3416-4db3-a6df-dd2b98286557/datasets")

    r.raise_for_status()
    groups = r.json()["value"]

    for group in groups:
        pprint(group)
