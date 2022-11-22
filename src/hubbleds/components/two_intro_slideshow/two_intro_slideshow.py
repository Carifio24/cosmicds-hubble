import ipyvuetify as v
from cosmicds.cds_glue_state import CDSGlueState
from cosmicds.utils import load_template
from traitlets import Int, Bool, Unicode, List, Float

from ...utils import DISTANCE_CONSTANT


# theme_colors()

class TwoIntroSlideShow(v.VuetifyTemplate):
    template = load_template(
        "two_intro_slideshow.vue", __file__, traitlet=True).tag(sync=True)
    step = Int(0).tag(sync=True)
    length = Int(13).tag(sync=True)
    dialog = Bool(False).tag(sync=True)
    currentTitle = Unicode("").tag(sync=True)
    state = CDSGlueState().tag(sync=True)
    max_step_completed = Int(0).tag(sync=True)
    interact_steps = List([7, 9]).tag(sync=True)
    two_intro_complete = Bool(False).tag(sync=True)
    show_team_interface = Bool(False).tag(sync=True)
    # exploration_complete = Bool(False).tag(sync=True)
    # intro_complete = Bool(False).tag(sync=True)
    distance_const = Float().tag(sync=True)

    _titles = [
        "1920's Astronomy",
        "1920's Astronomy",
        "How can we know how far away something is?",
        "How can we know how far away something is?",
        "How can we know how far away something is?",
        "How can we know how far away something is?",
        "Galaxy Distances",
        "Galaxy Distances",
        "Galaxy Distances",
        "Galaxy Distances",
        "Galaxy Distances",
        "Galaxy Distances",
        "Galaxy Distances"
    ]
    _default_title = "1920's Astronomy"

    def __init__(self, stage_state, app_state, *args, **kwargs):
        self.state = stage_state
        self.show_team_interface = app_state.show_team_interface
        self.distance_const = DISTANCE_CONSTANT
        self.currentTitle = self._default_title

        def update_title(change):
            index = change["new"]
            if index in range(len(self._titles)):
                self.currentTitle = self._titles[index]
            else:
                self.currentTitle = self._default_title

        self.observe(update_title, names=["step"])

        super().__init__(*args, **kwargs)
