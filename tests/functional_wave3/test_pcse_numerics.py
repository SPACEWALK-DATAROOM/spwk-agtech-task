"""Actual source contracts: pcse_numerics."""
from types import SimpleNamespace
import numpy as np
import pytest
from .loader import load

def test_reward_is_terminal_income_minus_actual_irrigation_and_nutrient_costs():
    ns=load('spwk_agtech/pcse_env.py',['get_profit','get_reward'])
    state=np.zeros(11);state[3]=1000
    action=np.zeros(13);action[9:]=[2,4,5,6]
    cost=10+1+2.3+2.22
    assert ns['get_profit'](state,action,False)==pytest.approx(-cost)
    assert ns['get_reward'](None,state,action,True)==pytest.approx(279.34-cost)

def test_normalization_roundtrip_clips_observations_and_actions():
    ns=load('spwk_agtech/pcse_env.py',['norm','denorm'],'PcseEnv')
    value=SimpleNamespace(action_min=np.array([0.,10.]),action_max=np.array([10.,30.]),obs_min=np.array([0.,10.]),obs_max=np.array([10.,30.]))
    physical=np.array([5.,20.])
    np.testing.assert_allclose(ns['denorm'](value,ns['norm'](value,physical,'act'),'act'),physical)
    np.testing.assert_allclose(ns['norm'](value,np.array([-5.,50.]),'obs'),[-1,1])
    np.testing.assert_allclose(ns['denorm'](value,np.array([-2.,2.]),'act'),[0,30])
