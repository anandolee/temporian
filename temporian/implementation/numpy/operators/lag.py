from typing import Dict

from temporian.core.data.duration import duration_abbreviation
from temporian.core.operators.lag import LagOperator
from temporian.implementation.numpy.data.event import NumpyEvent
from temporian.implementation.numpy.data.feature import NumpyFeature
from temporian.implementation.numpy.data.sampling import NumpySampling
from temporian.implementation.numpy import implementation_lib
from temporian.implementation.numpy.operators.base import OperatorImplementation


class LagNumpyImplementation(OperatorImplementation):
    def __init__(self, operator: LagOperator) -> None:
        super().__init__(operator)

    def __call__(self, event: NumpyEvent) -> Dict[str, NumpyEvent]:
        duration = self.operator.attributes["duration"]

        sampling_data = {}
        output_data = {}

        for index, timestamps in event.sampling.data.items():
            sampling_data[index] = timestamps + duration
            output_data[index] = []
            for feature in event.data[index]:
                new_feature = NumpyFeature(
                    data=feature.data,
                    name=feature.name,
                )
                output_data[index].append(new_feature)

        new_sampling = NumpySampling(
            data=sampling_data,
            index=event.sampling.index.copy(),
            is_unix_timestamp=event.sampling.is_unix_timestamp,
        )
        output_event = NumpyEvent(data=output_data, sampling=new_sampling)

        return {"event": output_event}


implementation_lib.register_operator_implementation(
    LagOperator, LagNumpyImplementation
)
