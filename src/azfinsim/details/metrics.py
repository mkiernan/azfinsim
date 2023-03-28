from opencensus.stats import measure as measure_module
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import view as view_module
from opencensus.stats import stats as stats_module
from opencensus.tags import TagMap, TagKey, TagValue

class Metrics:
    def __init__(self, config: dict, **kwargs) -> None:
        self.measures = {}
        self.views = {}
        self.tags = {}
        self.mmap = stats_module.stats.stats_recorder.new_measurement_map()
        self.config = config

        self.tmap = TagMap()
        for key, value in kwargs.items():
            self.tags[key] = TagKey(key)
            self.tmap.insert(self.tags[key], TagValue(str(value)))

        self._init_metrics()

    def _init_metrics(self):
        for measure, config in self.config.items():
            if config["type"] == "float":
                self.measures[measure] = measure_module.MeasureFloat(
                    measure, config["description"], config["unit"])
            elif config["type"] == "int":
                self.measures[measure] = measure_module.MeasureInt(
                    measure, config["description"], config["unit"])
            else:
                raise ValueError("Unknown metric type")
            
            if config["aggregation"] == "sum":
                aggr = aggregation_module.SumAggregation()
            elif config["aggregation"] == "last_value":
                aggr = aggregation_module.LastValueAggregation()
            else:
                raise ValueError("Unknown aggregation type")

            self.views[measure] = view_module.View(
                measure, config["description"], list(self.tags.keys()), self.measures[measure], aggr)

        # register views
        for view in self.views.values():
            stats_module.stats.view_manager.register_view(view)

    def put(self, measure, value):
        if self.config[measure]["type"] == "float":
            self.mmap.measure_float_put(self.measures[measure], value)
        elif self.config[measure]["type"] == "int":
            self.mmap.measure_int_put(self.measures[measure], value)
        else:
            raise ValueError("Unknown metric type")
        
    def record(self):
        self.mmap.record(self.tmap)
