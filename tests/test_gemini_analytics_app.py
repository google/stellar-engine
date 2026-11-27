# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the Gemini Enterprise Streamlit analytics dashboard."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock

APP_PATH = (
    Path(__file__).resolve().parent.parent
    / "blueprints"
    / "gemini-enterprise"
    / "analytics"
    / "app.py"
)


class _NotFound(Exception):
    """Minimal stand-in for google.api_core.exceptions.NotFound."""


class _SeriesStub:
    """Minimal Pandas Series stand-in for column operations."""

    def __init__(self, values):
        self._values = list(values)

    def nunique(self):
        return len(set(self._values))

    def astype(self, conv):
        return _SeriesStub([conv(v) for v in self._values])

    def __eq__(self, other):
        return [v == other for v in self._values]


class _DataFrameStub:
    """Minimal Pandas DataFrame stand-in for analytics/app.py tests."""

    def __init__(self, rows=None):
        self._rows = list(rows or [])

    @property
    def empty(self):
        return len(self._rows) == 0

    def __len__(self):
        return len(self._rows)

    def __getitem__(self, key):
        if isinstance(key, str):
            if self.empty or key not in self._rows[0]:
                raise KeyError(key)
            return _SeriesStub(row[key] for row in self._rows)
        if isinstance(key, list):
            return _DataFrameStub(
                [row for row, keep in zip(self._rows, key) if keep]
            )
        raise KeyError(key)

    def __setitem__(self, key, value):
        values = value._values if isinstance(value, _SeriesStub) else value
        for row, item in zip(self._rows, values):
            row[key] = item

    def groupby(self, cols):
        return _GroupByStub(self._rows, cols)

    def sort_values(self, by=None, ascending=True):
        return _DataFrameStub(
            sorted(
                self._rows,
                key=lambda row: row[by],
                reverse=not ascending,
            )
        )


class _GroupByStub:
    """Minimal groupby stub supporting .size() and column .nunique()."""

    def __init__(self, rows, cols):
        self._rows = rows
        self._cols = [cols] if isinstance(cols, str) else list(cols)

    def size(self):
        return _GroupSeriesStub(self._rows, self._cols, count_mode=True)

    def __getitem__(self, col):
        return _GroupSeriesStub(
            self._rows, self._cols, value_col=col, count_mode=False
        )


class _GroupSeriesStub:
    """Minimal grouped Series stub supporting .mean() and .reset_index()."""

    def __init__(self, rows, cols, value_col=None, count_mode=False):
        self._groups = {}
        for row in rows:
            key = tuple(row[c] for c in cols)
            bucket = self._groups.setdefault(key, [])
            bucket.append(1 if count_mode else row[value_col])
        self._cols = cols

    def nunique(self):
        self._counts = {k: len(set(v)) for k, v in self._groups.items()}
        return self

    def mean(self):
        counts = getattr(
            self, "_counts", {k: len(v) for k, v in self._groups.items()}
        )
        return sum(counts.values()) / len(counts) if counts else 0.0

    def reset_index(self, name="value"):
        counts = getattr(
            self, "_counts", {k: len(v) for k, v in self._groups.items()}
        )
        out = []
        for key, val in counts.items():
            row = dict(zip(self._cols, key))
            row[name] = val
            out.append(row)
        return _DataFrameStub(out)


class _Ctx:
    """Context manager stub for Streamlit tabs and columns."""

    def __init__(self):
        self.metric = MagicMock()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _build_stub_modules(query_handler):
    """Build sys.modules stubs to import analytics/app.py cleanly."""
    google_mod = types.ModuleType("google")
    api_core_mod = types.ModuleType("google.api_core")
    exceptions_mod = types.ModuleType("google.api_core.exceptions")
    exceptions_mod.NotFound = _NotFound
    cloud_mod = types.ModuleType("google.cloud")
    bq_mod = types.ModuleType("google.cloud.bigquery")

    client_inst = MagicMock()
    client_inst.query.side_effect = query_handler
    bq_mod.Client = MagicMock(return_value=client_inst)
    bq_mod.QueryJobConfig = MagicMock(return_value=MagicMock())
    bq_mod.ScalarQueryParameter = MagicMock(return_value=MagicMock())

    pd_mod = types.ModuleType("pandas")
    pd_mod.DataFrame = _DataFrameStub

    plotly_mod = types.ModuleType("plotly")
    px_mod = types.ModuleType("plotly.express")
    px_mod.line = MagicMock(return_value=MagicMock())
    px_mod.bar = MagicMock(return_value=MagicMock())
    px_mod.area = MagicMock(return_value=MagicMock())

    st_mod = MagicMock()
    st_mod.cache_data = lambda *args, **kwargs: lambda fn: fn
    st_mod.sidebar = MagicMock()
    st_mod.tabs.return_value = [_Ctx(), _Ctx(), _Ctx(), _Ctx()]
    st_mod.columns.side_effect = lambda n: [_Ctx() for _ in range(n)]

    return {
        "google": google_mod,
        "google.api_core": api_core_mod,
        "google.api_core.exceptions": exceptions_mod,
        "google.cloud": cloud_mod,
        "google.cloud.bigquery": bq_mod,
        "pandas": pd_mod,
        "plotly": plotly_mod,
        "plotly.express": px_mod,
        "streamlit": st_mod,
    }


class TestGeminiAnalyticsApp(unittest.TestCase):
    """Verify NotFound handling and empty DataFrame guards in app.py."""

    def _load_app_with_handler(self, query_handler, env=None):
        stubs = _build_stub_modules(query_handler)
        saved_modules = {k: sys.modules.get(k) for k in stubs}
        sys.modules.update(stubs)
        self.addCleanup(self._restore_modules, saved_modules)

        saved_env = {}
        env = env or {"PROJECT_ID": "test-project-1", "DATASET_ID": "ds_1"}
        for key, val in env.items():
            saved_env[key] = sys.modules["os"].environ.get(key)
            sys.modules["os"].environ[key] = val
        self.addCleanup(self._restore_env, saved_env)

        spec = importlib.util.spec_from_file_location("analytics_app", APP_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, stubs["streamlit"]

    @staticmethod
    def _restore_modules(saved):
        for name, mod in saved.items():
            if mod is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = mod

    @staticmethod
    def _restore_env(saved_env):
        import os

        for key, val in saved_env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    def test_not_found_and_empty_dataframes_do_not_crash(self):
        """Ensure missing BQ views return empty frames without KeyError."""

        def raise_not_found(*_args, **_kwargs):
            raise _NotFound(
                "Not found: Table vw_discovery_engine_user_activity"
            )

        module, st_mock = self._load_app_with_handler(raise_not_found)

        self.assertTrue(module.df_users.empty)
        self.assertTrue(module.df_sessions.empty)
        self.assertTrue(module.df_agents.empty)
        self.assertEqual(module.total_users, 0)
        self.assertEqual(module.total_sessions, 0)
        self.assertEqual(module.search_count, 0)
        self.assertEqual(module.answer_count, 0)
        self.assertEqual(st_mock.warning.call_count, 6)

    def test_populated_activity_metrics_compute_correctly(self):
        """Ensure search and answer counts aggregate non-empty rows."""
        user_rows = [
            {
                "principal": "a@example.com",
                "interaction_type": "Search",
                "operation_id": "op-1",
                "activity_date": "2026-01-01",
                "activity_week": "2026-01",
                "activity_month": "2026-01",
            },
            {
                "principal": "b@example.com",
                "interaction_type": "Assistant",
                "operation_id": "op-2",
                "activity_date": "2026-01-01",
                "activity_week": "2026-01",
                "activity_month": "2026-01",
            },
        ]
        session_rows = [
            {
                "session_id": "s-1",
                "session_date": "2026-01-01",
                "session_week": "2026-01",
            }
        ]
        agent_rows = [{"agent_id": 42, "principal": "a@example.com"}]

        def return_rows(query, **_kwargs):
            result = MagicMock()
            if "vw_discovery_engine_user_activity" in query:
                result.to_dataframe.return_value = _DataFrameStub(user_rows)
            elif "vw_discovery_engine_sessions" in query:
                result.to_dataframe.return_value = _DataFrameStub(session_rows)
            else:
                result.to_dataframe.return_value = _DataFrameStub(agent_rows)
            return result

        module, _st_mock = self._load_app_with_handler(return_rows)

        self.assertEqual(module.total_users, 2)
        self.assertEqual(module.total_sessions, 1)
        self.assertEqual(module.search_count, 1)
        self.assertEqual(module.answer_count, 1)


if __name__ == "__main__":
    unittest.main()
