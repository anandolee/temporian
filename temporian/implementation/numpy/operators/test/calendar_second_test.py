# Copyright 2021 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from absl.testing import absltest
import numpy as np
import pandas as pd

from temporian.core.operators.calendar.second import (
    CalendarSecondOperator,
)
from temporian.implementation.numpy.data.event import IndexData
from temporian.implementation.numpy.data.event import NumpyEvent
from temporian.implementation.numpy.operators.calendar.second import (
    CalendarSecondNumpyImplementation,
)


class CalendarSecondNumpyImplementationTest(absltest.TestCase):
    """Test numpy implementation of calendar_second operator."""

    def test_basic(self) -> None:
        "Basic test with flat event."
        input_event_data = NumpyEvent.from_dataframe(
            pd.DataFrame(
                data=[
                    [pd.to_datetime("1970-01-01 00:00:00", utc=True)],
                    [pd.to_datetime("1970-01-01 00:00:01", utc=True)],
                    [pd.to_datetime("1970-01-01 00:00:59", utc=True)],
                    [pd.to_datetime("2023-05-05 12:30:30", utc=True)],
                    [pd.to_datetime("2023-12-12 23:59:59", utc=True)],
                ],
                columns=["timestamp"],
            ),
        )
        input_event = input_event_data.schema()
        output_event_data = NumpyEvent(
            data={
                (): IndexData(
                    [np.array([0, 1, 59, 30, 59]).astype(np.int32)],
                    input_event_data.first_index_features().timestamps,
                ),
            },
            feature_names="calendar_second",
            index_names=[],
        )
        operator = CalendarSecondOperator(input_event)
        impl = CalendarSecondNumpyImplementation(operator)
        output = impl.call(sampling=input_event_data)

        self.assertTrue(output_event_data == output["event"])
        self.assertTrue(
            output["event"].first_index_features().features[0].dtype == np.int32
        )


if __name__ == "__main__":
    absltest.main()
