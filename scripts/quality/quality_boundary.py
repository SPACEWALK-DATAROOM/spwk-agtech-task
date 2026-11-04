"""Configuration and SDK/socket boundaries only; production algorithms are real."""
import socket
import sys
import types
from collections import defaultdict
from unittest.mock import patch, Mock

def blocked(*args,**kwargs):
    raise AssertionError("External service access is outside isolated campaign contracts")

def pytest_configure(config):
    config._quality_patches=[]
    for target in ["socket.socket.connect","socket.socket.connect_ex","socket.create_connection","socket.getaddrinfo","botocore.client.BaseClient._make_api_call"]:
        control=patch(target,blocked);control.start();config._quality_patches.append(control)
    # AWS Wrangler calls in these tests are S3 I/O boundaries, not dataframe algorithms.
    config._quality_previous_wr=sys.modules.get("awswrangler")
    wr=types.ModuleType("awswrangler")
    wr.s3=types.SimpleNamespace(**{name:Mock(side_effect=blocked) for name in ["read_parquet","read_csv","to_csv","to_parquet","list_objects","read_json","delete_objects","does_object_exist"]})
    exceptions=types.ModuleType("awswrangler.exceptions")
    exceptions.NoFilesFound=type("NoFilesFound",(Exception,),{})
    wr.exceptions=exceptions
    config._quality_previous_wr_exceptions=sys.modules.get("awswrangler.exceptions")
    sys.modules["awswrangler.exceptions"]=exceptions
    sys.modules["awswrangler"]=wr
    config._quality_previous_env=sys.modules.get("app.env")
    env=types.ModuleType("app.env")
    env.RDS=defaultdict(lambda:"postgresql://fixture:fixture@offline.invalid/fixture")
    sys.modules["app.env"]=env

def pytest_unconfigure(config):
    for control in reversed(getattr(config,"_quality_patches",[])):control.stop()
    wr=getattr(config,"_quality_previous_wr",None)
    if wr is None:sys.modules.pop("awswrangler",None)
    else:sys.modules["awswrangler"]=wr
    prior_exceptions=getattr(config,"_quality_previous_wr_exceptions",None)
    if prior_exceptions is None:sys.modules.pop("awswrangler.exceptions",None)
    else:sys.modules["awswrangler.exceptions"]=prior_exceptions
    previous=getattr(config,"_quality_previous_env",None)
    if previous is None:sys.modules.pop("app.env",None)
    else:sys.modules["app.env"]=previous
