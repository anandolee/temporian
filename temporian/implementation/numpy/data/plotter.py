"""Plotting utility."""

from typing import NamedTuple, Optional, Union, List, Any

import numpy as np
from enum import Enum

from temporian.core.data import duration
from temporian.implementation.numpy.data.event import NumpyEvent


class Style(Enum):
    """Plotting style."""

    # Determine the style according to the data.
    auto = "auto"
    # Connect numerical values with a line.
    line = "line"
    # A discreet marker showing a feature value.
    marker = "marker"
    # A discreet marker not showing a feature value.
    vline = "vline"


class Options(NamedTuple):
    """Options for plotting."""

    backend: Optional[str]
    height_per_plot_px: int
    width_px: int
    max_points: Optional[int]
    min_time: Optional[duration.Timestamp]
    max_time: Optional[duration.Timestamp]
    max_num_plots: int
    style: Style
    interactive: bool


def plot(
    events: Union[List[NumpyEvent], NumpyEvent],
    indexes: Optional[Union[Any, tuple, List[tuple]]] = None,
    width_px: int = 1024,
    height_per_plot_px: int = 150,
    max_points: Optional[int] = None,
    min_time: Optional[duration.Timestamp] = None,
    max_time: Optional[duration.Timestamp] = None,
    max_num_plots: int = 20,
    style: Union[Style, str] = Style.auto,
    return_fig: bool = False,
    interactive: bool = False,
    backend: Optional[str] = None,
):
    """Plots an event.

    Args:
        events: Single event, or list of events, to plot.
        indexes: The index or list of indexes to plot. If index=None, plots all
            the available indexes. Indexes should be provided as single value
            (e.g. string) or tuple of values. Example: index="a", index=("a",),
            index=("a", "b",), index=["a", "b"], index=[("a", "b"), ("a", "c")].
        width_px: Width of the figure in pixel.
        height_per_plot_px: Height of each sub-plot (one per feature) in pixel.
        max_points: Maximum number of points to plot.
        min_time: If set, only plot events after it.
        max_time: If set, only plot events before it.
        max_num_plots: Maximum number of plots to display. If more plots are
            available, only plot the first `max_num_plots` ones and print a
            warning.
        return_fig: If true, returns the figure object. The figure object
            depends on the backend.
        interactive: If true, creates an interractive plotting. interactive=True
            effectively selects a backend that support interractive plotting.
        backend: Plotting library to use. Possible values are: matplotlib,
            bokeh.
    """

    original_indexes = indexes

    if not isinstance(events, list):
        events = [events]

    if len(events) == 0:
        raise ValueError("Events is empty")

    if indexes is None:
        # All the indexes
        indexes = list(events[0].data.keys())

    elif isinstance(indexes, tuple):
        # e.g. indexes=("a",)
        indexes = [indexes]

    elif isinstance(indexes, list):
        # e.g. indexes=["a", ("b",)]
        indexes = [v if isinstance(v, tuple) else (v,) for v in indexes]

    else:
        # e.g. indexes="a"
        indexes = [(indexes,)]

    for index in indexes:
        if not isinstance(index, tuple):
            raise ValueError(
                "An index should be a tuple or a list of tuples. Instead"
                f' receives "indexes={original_indexes}"'
            )

    if isinstance(style, str):
        style = Style[style]
    assert isinstance(style, Style)

    options = Options(
        interactive=interactive,
        backend=backend,
        width_px=width_px,
        height_per_plot_px=height_per_plot_px,
        max_points=max_points,
        min_time=min_time,
        max_time=max_time,
        max_num_plots=max_num_plots,
        style=style,
    )

    if backend is None:
        backend = "bokeh" if interactive else "matplotlib"

    if backend not in BACKENDS:
        raise ValueError(
            f"Unknown plotting backend {backend}. Available "
            f"backends: {BACKENDS}"
        )

    try:
        fig = BACKENDS[backend](events=events, indexes=indexes, options=options)
    except ImportError:
        print(error_message_import_backend(backend))
        raise

    return fig if return_fig else None


def get_num_plots(
    events: List[NumpyEvent], indexes: List[tuple], options: Options
):
    """Computes the number of sub-plots."""

    num_plots = 0
    for index in indexes:
        for event in events:
            if index not in event.data:
                raise ValueError(
                    f"Index '{index}' does not exist in event. Check the"
                    " available indexes with 'event.index' and provide one of"
                    " those index to the 'index' argument of 'plot'."
                    ' Alternatively, set "index=None" to select a random'
                    f" index value (e.g., {event.first_index_key()}."
                )
            num_features = len(event.feature_names)
            if num_features == 0:
                # We plot the sampling
                num_features = 1
            num_plots += num_features

    if num_plots == 0:
        raise ValueError("There is nothing to plot.")

    if num_plots > options.max_num_plots:
        print(
            f"The number of plots ({num_plots}) is larger than "
            f'"options.max_num_plots={options.max_num_plots}". Only the first '
            "plots will be printed."
        )
        num_plots = options.max_num_plots

    return num_plots


def auto_style(uniform: bool, xs, ys) -> Style:
    """Finds the best plotting style."""

    if len(ys) == 0:
        all_ys_are_equal = True
    else:
        all_ys_are_equal = np.all(ys == ys[0])

    if not uniform and (len(xs) <= 1000 or all_ys_are_equal):
        return Style.marker
    else:
        return Style.line


def is_uniform(xs) -> bool:
    """Checks if timestamps are uniformly sampled."""

    diff = np.diff(xs)
    if len(diff) == 0:
        return True
    return np.allclose(diff, diff[0])


from temporian.implementation.numpy.data.plotter_bokeh import plot_bokeh
from temporian.implementation.numpy.data.plotter_matplotlib import (
    plot_matplotlib,
)

BACKENDS = {"matplotlib": plot_matplotlib, "bokeh": plot_bokeh}


def error_message_import_backend(backend: str) -> str:
    return (
        f"Cannot plot with selected backend={backend}. Solutions: (1) Install"
        f" {backend} e.g. 'pip install {backend}', or (2) use a different"
        " plotting backen, for example with 'plot(..., backend=\"<other"
        f' backend>"). The supported backends are: {list(BACKENDS.keys())}.'
    )
