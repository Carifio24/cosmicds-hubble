from cosmicds.state import GlobalState, BaseState
from glue.core.data_factories import load_data
from pathlib import Path

from typing import Optional, Callable, Any, Tuple, List

from hubbleds.data_management import HUBBLE_1929_DATA_LABEL, HUBBLE_KEY_DATA_LABEL
from hubbleds.data_models.student import StudentData
from hubbleds.free_response import FreeResponseDict, update_free_response
from solara import Reactive
from dataclasses import dataclass, field, is_dataclass
from hubbleds.decorators import computed_property


@dataclass
class MCScore:
    tag: str = field(init=True)
    _score_dict: Reactive[dict[str, int]] = field(
        default_factory=lambda: Reactive({})
    )

    def update(self, score, choice, tries, wrong_attempts):
        print("updating", self.tag, score, choice, tries, wrong_attempts)
        self._score_dict.set(
            {
                "score": score,
                "choice": choice,
                "tries": tries,
                "wrong_attempts": wrong_attempts,
            }
        )

    def toJSON(self):
        return {
            "tag": self.tag,
            "score": self._score_dict.value.get("score", None),
            "choice": self._score_dict.value.get("choice", None),
            "tries": self._score_dict.value.get("tries", 0),
            "wrong_attempts": self._score_dict.value.get("wrong_attempts", 0),
        }

    def __repr__(self):
        return f"MCScore({self.toJSON()})"

    @computed_property
    def completed(self):
        return self._score_dict.value.get("score", None) is not None


@dataclass
class LocalState(BaseState):
    debug_mode: Reactive[bool] = field(default=Reactive(False))
    title: Reactive[str] = field(default=Reactive("Hubble's Law"))
    stages: Reactive[list] = field(default=Reactive([]))
    measurements: Reactive[dict] = field(default=Reactive({}))
    calculations: Reactive[dict] = field(default=Reactive({}))
    validation_failure_counts: Reactive[dict] = field(default=Reactive({}))
    has_best_fit_galaxy: Reactive[bool] = field(default=Reactive(False))
    enough_students_ready: Reactive[bool] = field(default=Reactive(False))
    started: Reactive[bool] = field(default=Reactive(False))
    class_data_students: Reactive[list] = field(default=Reactive([]))
    class_data_info: Reactive[dict] = field(default=Reactive({}))
    mc_scoring: Reactive[dict[str, MCScore]] = field(default=Reactive({}))
    free_responses: FreeResponseDict = field(
        default_factory=FreeResponseDict
    )
    student_data: Reactive[StudentData] = field(
        default_factory=lambda: Reactive(StudentData(measurements=[]))
    )
    example_data: Reactive[StudentData] = field(
        default_factory=lambda: Reactive(StudentData(measurements=[]))
    )

    def question_completed(self, qtag: str):
        if qtag in self.mc_scoring.value:
            return self.mc_scoring.value[qtag].completed().value  # type: ignore
        return False

    def from_dict(self, d):
        # TODO: We're overriding the base class method here, this needs to be
        #  revisited once we've figured out serialization of pydantic annotated
        #  types (ask Nick).
        def _inner_dict(dd, parent):
            for k, v in dd.items():
                attr = getattr(parent, k)

                if k in ['example_data', 'student_data']:
                    # v = StudentData(**v)
                    return {}

                if isinstance(attr, Reactive):
                    attr.set(v)
                elif is_dataclass(attr):
                    _inner_dict(v, attr)

        _inner_dict(d, self)


GLOBAL_STATE = GlobalState()
LOCAL_STATE = LocalState()

# add a csv file to the data collection


def add_link(from_dc_name, from_att, to_dc_name, to_att):
    from_dc = GLOBAL_STATE.data_collection[from_dc_name]
    to_dc = GLOBAL_STATE.data_collection[to_dc_name]
    GLOBAL_STATE._glue_app.add_link(from_dc, from_att, to_dc, to_att)


data_dir = Path(__file__).parent / "data"

try:
    GLOBAL_STATE.data_collection.append(
        load_data(data_dir / f"{HUBBLE_KEY_DATA_LABEL}.csv")
    )
    GLOBAL_STATE.data_collection.append(
        load_data(data_dir / f"{HUBBLE_1929_DATA_LABEL}.csv")
    )

    add_link(
        HUBBLE_1929_DATA_LABEL,
        "Distance (Mpc)",
        HUBBLE_KEY_DATA_LABEL,
        "Distance (Mpc)",
    )
    add_link(
        HUBBLE_1929_DATA_LABEL,
        "Tweaked Velocity (km/s)",
        HUBBLE_KEY_DATA_LABEL,
        "Velocity (km/s)",
    )
except:
    print("Data already loaded into Glue.")


# create handlers for mc_radiogroup
def on_init_response(
    local_state: LocalState, tag: str, callback: Optional[Callable] = None
):
    print("onInitResponse")
    # print(tag not in component_state.mc_scoring.value.keys())
    if tag not in local_state.mc_scoring.value.keys():
        print("adding tag", tag)
        mc_scoring = local_state.mc_scoring.value
        print(MCScore(tag=tag))
        mc_scoring[tag] = MCScore(tag=tag)
        print(mc_scoring)
        local_state.mc_scoring.set(mc_scoring)
        if callback is not None:
            callback(mc_scoring)
    else:
        print("tag already exists")


def on_mc_score(local_state, data, callback: Optional[Callable] = None):
    print("on_mc_score")
    mc_scoring = local_state.mc_scoring.value
    mc_scoring[data["tag"]].update(
        data["score"], data["choice"], data["tries"], data["wrong_attempts"]
    )
    local_state.mc_scoring.set(mc_scoring)
    if callback is not None:
        callback(mc_scoring)


def mc_callback(event, local_state, callback: Optional[Callable] = None):
    # mc-initialize-callback returns data which is a string
    if event[0] == "mc-initialize-response":
        return on_init_response(
            local_state=local_state, tag=event[1], callback=callback
        )
    # mc-score event returns a data which is an mc-score dictionary
    elif event[0] == "mc-score":
        return on_mc_score(local_state=local_state, data=event[1], callback=callback)
    else:
        print(f"Unknown event in mc_callback: <<{event}>> ")


def mc_serialize_score(mc_score=None):
    if mc_score is None:
        return None
    return mc_score.toJSON()


def fr_callback(
    event: Tuple[str, dict[str, str]],
    local_state: LocalState,
    response_callback: Optional[Callable] = None,
):
    """
    Free Response callback function

    response_callback: Optional callback that takes in the response as an argument
        An example would be to set a value
    """
    print("fr_callback", event)
    if event[0] == "fr-initialize":
        # by using get_free_response in the Page, we can avoid separately
        # initializing the free response initialize_free_
        # response(local_state.free_responses, tag=event[1]['tag'])
        pass
    elif event[0] == "fr-update":
        update_free_response(
            local_state.free_responses,
            tag=event[1]["tag"],
            response=event[1]["response"],
        )
        if response_callback is not None:
            if (len(event) > 1) and ("response" in event[1]):
                response_callback(event[1]["response"])
    else:
        raise ValueError(f"Unknown event in fr_callback: <<{event}>> ")
