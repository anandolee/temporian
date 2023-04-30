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

"""Filter operator class and public API function definition."""

from typing import Optional

from temporian.core import operator_lib
from temporian.core.data.dtype import DType
from temporian.core.data.feature import Feature
from temporian.core.data.event import Event
from temporian.core.data.sampling import Sampling
from temporian.core.operators.base import Operator
from temporian.proto import core_pb2 as pb


class FilterOperator(Operator):
    def __init__(self, event: Event, condition: Event):
        super().__init__()

        # check that condition is a single feature
        if len(condition.features) != 1:
            raise ValueError(
                "Condition must be a single feature. Got"
                f" {len(condition.features)} instead."
            )

        # check that condition is a boolean feature
        if condition.features[0].dtype != DType.BOOLEAN:
            raise ValueError(
                "Condition must be a boolean feature. Got"
                f" {condition.features[0].dtype} instead."
            )

        # check both events have same index
        if event.sampling.index != condition.sampling.index:
            raise ValueError(
                "Event and condition must have the same sampling. Got"
                f" {event.sampling} and {condition.sampling} instead."
            )

        # inputs
        self.add_input("event", event)
        self.add_input("condition", condition)

        output_sampling = Sampling(
            index_levels=event.sampling.index, creator=self
        )

        self.condition_name = condition.features[0].name

        # outputs
        output_features = [  # pylint: disable=g-complex-comprehension
            Feature(
                name=f.name,
                dtype=f.dtype,
                sampling=output_sampling,
                creator=self,
            )
            for f in event.features
        ]

        self.add_output(
            "event",
            Event(
                features=output_features,
                sampling=output_sampling,
                creator=self,
            ),
        )

        self.check()

    @classmethod
    def build_op_definition(cls) -> pb.OperatorDef:
        return pb.OperatorDef(
            key="FILTER",
            attributes=[],
            inputs=[
                pb.OperatorDef.Input(key="event"),
                pb.OperatorDef.Input(key="condition"),
            ],
            outputs=[pb.OperatorDef.Output(key="event")],
        )


operator_lib.register_operator(FilterOperator)


# pylint: disable=redefined-builtin
def filter(
    event: Event,
    condition: Optional[Event] = None,
) -> Event:
    """Filters out timestamps in an event for which a condition is false.

    Each timestamp in `event` is only kept if the corresponding value for that
    timestamp in `condition` is `True`.

    `event` and `condition` must have the same sampling.

    filter(x) is equivalent to filter(x,x). filter(x) can be used to convert
    a boolean mask into a timestamps. For example:
        Input:
            timestamps: 1 2 3
            value: True False True
        Output:
            timestamps: 1 3
            value: True True

    Args:
        event: Event to filter.
        condition: Event with a single boolean feature condition.

    Returns:
        Filtered event.
    """

    if condition is None:
        condition = event

    return FilterOperator(event, condition).outputs["event"]
