import unittest

from MLPipeline.pipeline import Pipeline
from MLPipeline.pipeline_builder import Builder, PipelineParsingError
from Tests.utils import create_dummy_pipeline_dict


class ExceptionTestCase(unittest.TestCase):
    """
    tests for pipeline building + if are the exceptions properly raised
    """

    def setUp(self):
        self.pipeline = create_dummy_pipeline_dict(
            **{
                'depth': 1,
                'no_inputs': 1,
                'no_outputs': 1,
                'max_components_per_level': 1,
            }
        )
        self.inputs = self.pipeline['pipeline']['inputs']
        self.builder = Builder()

    """Pipeline construction is thoroughly tested but the rest of the code isn't.
    """
    def test_pipeline_key_missing(self):
        self.pipeline.pop('pipeline')
        self.builder.parsed_yaml = self.pipeline
        self.builder.pass_command_line_inputs({i: '' for i in self.inputs})
        with self.assertRaises(PipelineParsingError):
            self.builder.build_pipeline(verbose=False)

    def test_pipeline_name_missing(self):
        self.pipeline['pipeline'].pop('name')
        self.builder.parsed_yaml = self.pipeline
        self.builder.pass_command_line_inputs({i: '' for i in self.inputs})
        with self.assertRaises(PipelineParsingError):
            self.builder.build_pipeline(verbose=False)

    def test_pipeline_inputs_missing(self):
        self.pipeline['pipeline'].pop('inputs')
        self.builder.parsed_yaml = self.pipeline
        self.builder.pass_command_line_inputs({i: '' for i in self.inputs})
        with self.assertRaises(PipelineParsingError):
            self.builder.build_pipeline(verbose=False)

    def test_pipeline_components_missing(self):
        self.pipeline['pipeline'].pop('components')
        self.builder.parsed_yaml = self.pipeline
        self.builder.pass_command_line_inputs({i: '' for i in self.inputs})
        with self.assertRaises(PipelineParsingError):
            self.builder.build_pipeline(verbose=False)

    def test_pipeline_component_multiple_entries(self):
        self.pipeline['pipeline']['components'][0]['second_name'] = 'foo'
        self.builder.parsed_yaml = self.pipeline
        self.builder.pass_command_line_inputs({i: '' for i in self.inputs})
        with self.assertRaises(PipelineParsingError):
            self.builder.build_pipeline(verbose=False)

    def test_pipeline_component_runner_missing(self):
        list(self.pipeline['pipeline']['components'][0].values())[0].pop('runner')
        self.builder.parsed_yaml = self.pipeline
        self.builder.pass_command_line_inputs({i: '' for i in self.inputs})
        with self.assertRaises(PipelineParsingError):
            self.builder.build_pipeline(verbose=False)

    def test_pipeline_component_inputs_missing(self):
        list(self.pipeline['pipeline']['components'][0].values())[0].pop('inputs')
        self.builder.parsed_yaml = self.pipeline
        self.builder.pass_command_line_inputs({i: '' for i in self.inputs})
        with self.assertRaises(PipelineParsingError):
            self.builder.build_pipeline(verbose=False)

    def test_pipeline_component_outputs_missing(self):
        list(self.pipeline['pipeline']['components'][0].values())[0].pop('outputs')
        self.builder.parsed_yaml = self.pipeline
        self.builder.pass_command_line_inputs({i: '' for i in self.inputs})
        with self.assertRaises(PipelineParsingError):
            self.builder.build_pipeline(verbose=False)

    def test_missing_command_line_input(self):
        self.builder.parsed_yaml = self.pipeline
        with self.assertRaises(PipelineParsingError):
            self.builder.build_pipeline(verbose=False)

    def test_success(self):
        self.builder.parsed_yaml = self.pipeline
        self.builder.pass_command_line_inputs({i: '' for i in self.inputs})
        build_pipeline = self.builder.build_pipeline(verbose=False)
        self.assertEqual(type(build_pipeline), Pipeline)
