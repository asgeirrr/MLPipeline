import yaml

from MLPipeline.consumable import Consumable
from MLPipeline.pipeline import Pipeline
from MLPipeline.pipeline_task import TaskFactory
from MLPipeline.utils import is_subset_of, list_of_dicts_to_dict


class PipelineParsingError(Exception):

    def __init__(self, message: str):
        """No need to override __init__ when it's not doing anything different than
        Exception.__init__.
        """
        super().__init__(message)

"""
The existence of this class seems unjustified.
    1. The individual steps are always run together. A function
       `build_pipeline(parsed_yaml, command_line_inputs)` would be enough.
       Using a class instead of a function unnecessarily adds complexity.
    2. It binds together parsing of the yaml with pipeline construction which imho violates
       separation of concerns and makes the code less re-usable. In future, we could get
       pipeline definitions from a different source, for instance from an API, and this class
       could not be reused as is.
"""
class Builder:
    """Class for instantiating the pipeline:

    flow:
    1. instantiate
    2. load_yml
    3. pass_command_line_inputs
    4. build_pipeline to get Pipeline
    """

    def __init__(self):
        self.parsed_yaml = {}
        self.command_line_inputs = {}

    def load_yaml(self, filename: str) -> None:
        """
        :param filename: path to pipeline.yaml file
        """
        with open(filename) as yaml_file:
            self.parsed_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

    def pass_command_line_inputs(self, command_line_inputs: dict) -> None:
        """pass command line inputs as dict to pipeline"""
        self.command_line_inputs.update(command_line_inputs)

    def build_pipeline(self, bad_yaml=False, verbose=True) -> Pipeline:
        """
        Function that returns pipeline when fed with .yaml and inputs
        Implementing for one pipeline per yaml, could be easily extended.
        :param bad_yaml: turns on/off parsing of all-list-yaml, default=False
        :param verbose: turns on/off verbosity during build (anoying in tests), default=False
        :return: returns Pipeline instance
        """

        if verbose:
            """You're basically doing an ad-hoc re-implementation of log levels here. If you did
            logging.debug("Building pipeline...") you could control the verbosity in one place
            by setting a log level (possibly passed from the command line with the traditional -v
            switch). Plus the CLI is quite talkative by default violating the good-old Unix rule
            that silence is gold.
            """
            print("Building pipeline...")

        # check of the base level definition
        # if you made original yaml and you read this - look here https://en.wikipedia.org/wiki/YAML
        if self.parsed_yaml.get('pipeline'):
            if bad_yaml:
                pipeline_content = list_of_dicts_to_dict(self.parsed_yaml['pipeline'])
            else:
                pipeline_content = self.parsed_yaml['pipeline']
        else:
            raise PipelineParsingError("Missing pipeline definition.")

        if not is_subset_of(
                ['name', 'inputs', 'outputs', 'components'],
                list(pipeline_content.keys())
        ):
            raise PipelineParsingError("Pipeline missing key attributes.")

        """This function is quite complex and pipeline initialization is scattered around.
        Personally, I'd split it to separate steps
            1. parse components (this would be a good candidate for a separate function)
            2. parse inputs and outputs
            3. initialize pipeline in one go with all the needed arguments.
        That way you could use Pipeline.__init__ to validate for free it has all the needed
        attributes.
        """
        pipeline = Pipeline(pipeline_content['name'])
        # now we have the pipeline lets start to feed it
        task_factory_instance = TaskFactory()
        for component in pipeline_content['components']:

            if len(component) != 1:
                raise PipelineParsingError(
                    "Component root should be list of dicts of length one with its component.name as a key!"
                )
            else:
                c_name = list(component.keys())[0]

            if bad_yaml:
                component_dict = list_of_dicts_to_dict(component[c_name])
            else:
                component_dict = component[c_name]
            # checking if task contain all required sections
            if not is_subset_of(['runner', 'inputs', 'outputs'], list(component_dict.keys())):
                raise PipelineParsingError(f'Component {c_name} missing one of the key arguments!')

            task_from_component = task_factory_instance.spawn_task(c_name, **component_dict)
            pipeline.add_task(task_from_component)

        # check if all pipeline inputs are declared on command line and add them one by one
        for pipeline_input in pipeline_content['inputs']:
            if pipeline_input in self.command_line_inputs:
                consumable_from_input = Consumable(pipeline_input, self.command_line_inputs[pipeline_input])
                pipeline.add_input(consumable_from_input)
            else:
                raise PipelineParsingError(
                    f"Pipeline declared input {pipeline_input} not found in command line inputs!")

        # this could be done in one shove, but there should be in principle CRUD
        # this way it would be easy to extend in future :)
        for pipeline_output in pipeline_content['outputs']:
            if pipeline_output not in pipeline.expected_outputs:
                pipeline.add_output(pipeline_output)

        return pipeline
