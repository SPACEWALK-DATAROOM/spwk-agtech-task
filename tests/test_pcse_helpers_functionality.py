import collections
import collections.abc
import datetime
import unittest

import numpy as np

# PCSE 5.4.2 imports collection ABCs removed from collections in Python 3.12.
for _name in ("Iterable", "Mapping", "MutableMapping", "Sequence", "MutableSequence"):
    if not hasattr(collections, _name):
        setattr(collections, _name, getattr(collections.abc, _name))

from pathlib import Path
import importlib.util
import gym
from spwk_agtech.const import ACTIONS, OBSERVATIONS
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pcse_contract_definitions',Path(__file__).parent/'functional_wave3/loader.py')
loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
# Module startup constructs/configures unrelated PCSE dependencies. Only the
# original class/function bodies used below execute, retaining actual gym.Env.
numerics=loader.load('spwk_agtech/pcse_env.py',['PcseEnv','get_profit','get_reward'],gym=gym,ACTIONS=ACTIONS,OBSERVATIONS=OBSERVATIONS)
PcseEnv=numerics['PcseEnv'];get_profit=numerics['get_profit'];get_reward=numerics['get_reward']
send_actions2engine=loader.load('spwk_agtech/utils.py',['send_actions2engine'],ACTIONS=ACTIONS,OBSERVATIONS=OBSERVATIONS)['send_actions2engine']


class WeatherRecord:
    pass


class EventDispatcher:
    def __init__(self):
        self.events_table = []
        self.days_with_events = set()


class EngineFixture:
    def __init__(self, day):
        self.day = day
        self.weather = WeatherRecord()
        self.requested_dates = []
        self.irrigation = EventDispatcher()
        self.npk = EventDispatcher()
        self.agromanager = type("AgromanagerFixture", (), {
            "timed_event_dispatchers": [[self.irrigation, self.npk]],
        })()

    def weatherdataprovider(self, date):
        self.requested_dates.append(date)
        return self.weather


class PCSEHelperFunctionalityTests(unittest.TestCase):
    def test_terminal_profit_includes_yield_revenue_and_input_costs(self):
        state = np.array([0, 0, 0, 2000])
        action = np.array([0] * 9 + [10, 100, 200, 300])

        self.assertAlmostEqual(get_profit(state, action, done=True), 280.68)
        self.assertAlmostEqual(get_reward(state, state, action, done=True), 280.68)

    def test_nonterminal_profit_excludes_yield_revenue(self):
        state = np.array([0, 0, 0, 2000])
        action = np.array([0] * 9 + [10, 100, 200, 300])

        self.assertAlmostEqual(get_profit(state, action, done=False), -278.0)
        self.assertEqual(get_profit(state, np.zeros(13), done=False), 0)

    def test_action_dispatch_updates_weather_and_schedules_irrigation_and_fertilizer(self):
        engine = EngineFixture(datetime.date(2024, 2, 28))
        actions = np.array([100, 10, 20, 1, 2, 0.1, 0.2, 0.3, 4, 5, 6, 7, 8], dtype=float)

        weather, irrigation, npk = send_actions2engine(actions, engine)

        next_day = datetime.date(2024, 2, 29)
        self.assertEqual(engine.requested_dates, [next_day])
        self.assertEqual(weather["IRRAD"], 100)
        self.assertEqual(weather["WIND"], 4)
        self.assertEqual(engine.weather.TMAX, 20)
        self.assertEqual(irrigation, {"amount": 5, "efficiency": 0.7})
        self.assertEqual(npk, {
            "N_amount": 6, "P_amount": 7, "K_amount": 8,
            "N_recovery": 0.7, "P_recovery": 0.7, "K_recovery": 0.7,
        })
        self.assertEqual(engine.irrigation.events_table, [{next_day: irrigation}])
        self.assertEqual(engine.npk.events_table, [{next_day: npk}])
        self.assertEqual(engine.irrigation.days_with_events, {next_day})
        self.assertEqual(engine.npk.days_with_events, {next_day})

    def test_nan_weather_is_skipped_and_invalid_npk_is_not_scheduled(self):
        engine = EngineFixture(datetime.date(2024, 1, 1))
        actions = np.array([100, np.nan, 20, 1, 2, 0.1, 0.2, 0.3, 4, np.nan, np.nan, 7, 8])

        weather, irrigation, _ = send_actions2engine(actions, engine)

        self.assertNotIn("TMIN", weather)
        self.assertFalse(hasattr(engine.weather, "TMIN"))
        self.assertTrue(np.isnan(irrigation["amount"]))
        self.assertEqual(engine.irrigation.events_table, [])
        self.assertEqual(engine.npk.events_table, [])

    def _normalization_fixture(self):
        env = object.__new__(PcseEnv)
        env.obs_min = np.array([v["min"] for v in OBSERVATIONS.values()], dtype=np.float32)
        env.obs_max = np.array([v["max"] for v in OBSERVATIONS.values()], dtype=np.float32)
        env.action_min = np.array([v["min"] for v in ACTIONS.values()], dtype=np.float32)
        env.action_max = np.array([v["max"] for v in ACTIONS.values()], dtype=np.float32)
        env.obs_name = list(OBSERVATIONS.keys())
        return env

    def test_observation_and_action_normalization_round_trip(self):
        env = self._normalization_fixture()
        observations = (env.obs_min + env.obs_max) / 2
        actions = (env.action_min + env.action_max) / 2

        np.testing.assert_allclose(env.norm(observations, "obs"), np.zeros_like(observations))
        np.testing.assert_allclose(env.norm(actions, "act"), np.zeros_like(actions))
        np.testing.assert_allclose(env.denorm(env.norm(observations, "obs"), "obs"), observations)
        np.testing.assert_allclose(env.denorm(env.norm(actions, "act"), "act"), actions)

    def test_observation_normalization_clips_values_to_agent_space(self):
        env = self._normalization_fixture()
        raw = env.obs_min - 1
        raw[-1] = env.obs_max[-1] + 1

        normalized = env.norm(raw, "obs")

        np.testing.assert_array_equal(normalized, np.array([-1] * (len(raw) - 1) + [1]))

    def test_get_obs_selects_configured_names_and_normalizes_in_order(self):
        env = self._normalization_fixture()
        expected = (env.obs_min + env.obs_max) / 2
        raw = dict(zip(env.obs_name, expected.tolist()))
        raw["unconfigured_extra"] = 9999

        observed = env.get_obs(raw, env.obs_name)

        self.assertEqual(observed.shape, (len(env.obs_name),))
        np.testing.assert_allclose(observed, np.zeros(len(env.obs_name)))

    def test_too_short_action_vector_is_rejected(self):
        with self.assertRaises(AssertionError):
            send_actions2engine(np.zeros(8), EngineFixture(datetime.date(2024, 1, 1)))


if __name__ == "__main__":
    unittest.main()
