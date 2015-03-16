from rally.benchmark.scenarios import base


class shaiker_controller(base.Scenario):
    """Sample plugin for shaiker."""

    @base.scenario()
    def sample_print(self):
        print "its work"
        print "controllers: ", self.context["controllers"]
        self.context["nodes"] = ["10", "11", "12"]
        print "nodes: ", self.context["nodes"]
