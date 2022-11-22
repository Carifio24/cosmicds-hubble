import ipyvuetify as v
from cosmicds.cds_glue_state import CDSGlueState
from cosmicds.utils import load_template
from echo import add_callback
from traitlets import Unicode


class DistanceSidebar(v.VuetifyTemplate):
    template = load_template("distance_sidebar.vue", __file__,
                             traitlet=True).tag(sync=True)
    state = CDSGlueState().tag(sync=True)
    angular_height = Unicode().tag(sync=True)
    angular_size = Unicode().tag(sync=True)
    galaxy_type = Unicode().tag(sync=True)

    def __init__(self, state, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = state
        add_callback(self.state, 'galaxy', self._on_galaxy_update)

    def _on_galaxy_update(self, galaxy):
        self.galaxy_type = galaxy["type"]
        self.angular_size = ""

    def vue_add_distance_data_point(self, _args=None):
        self.state.make_measurement = True
