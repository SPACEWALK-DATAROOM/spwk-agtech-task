"""Actual source contracts: nasapower_records."""
import logging
from types import SimpleNamespace
import pandas as pd
from .loader import load

def test_power_record_parser_removes_fill_rows_and_parses_leap_day():
    fn=load('spwk_agtech/nasapower.py',['_process_POWER_records'],'NASAPowerWeatherDataProvider')['_process_POWER_records']
    weather={'header':{'fill_value':-999},'properties':{'parameter':{'T2M':{'20240228':3,'20240229':4,'20240301':-999},'WS2M':{'20240228':2,'20240229':3,'20240301':4}}}}
    result=fn(SimpleNamespace(logger=logging.getLogger('offline'),power_variables=['T2M','WS2M']),weather)
    assert result.T2M.tolist()==[3,4]
    assert result.DAY.tolist()==[pd.Timestamp('2024-02-28'),pd.Timestamp('2024-02-29')]
