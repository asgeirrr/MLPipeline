import inspect
import random
import time
from typing import List, Tuple

from MLPipeline.consumable import Consumable


class AbstractTask:
    """abstract class for all runners which are defined in pipeline_runners"""

    def __init__(
            self,
            name: str,
            input_consumables: List[str] = None,
            output_consumables: List[str] = None,
    ):

        if input_consumables is None:
            self.input_consumables = []
        else:
            self.input_consumables = input_consumables

        if output_consumables is None:
            self.output_consumables = []
        else:
            self.output_consumables = output_consumables

        self.name = name
        self.generated_outputs: List[Consumable] = []

    def execute(self, input_consumables: List[Consumable]):
        raise Exception("Executing of AbstractTask is not what you should do! Overload the execute method fist!")

    def fake_execute(self, input_consumables: List[Consumable]) -> List[Consumable]:
        """performs fake execution of the task"""
        task_result = []
        # generate output Consumables
        for output in self.output_consumables:
            new_content = f"{[c.full_name for c in input_consumables]}" \
                          f"->" \
                          f"{self.name}" \
                          f"->" \
                          f"{self.name}.{output}"
            task_result.append(Consumable(output, new_content, self.name))
        return task_result

    def dummy_executor(self, inputs: List[Consumable], key: str, duration: Tuple[int, int] = (1, 5)) -> None:
        """This is just dummy executor which i am gonna use in runners to make my work easier"""
        print(f'Starting execution of {self.name}')
        time.sleep(random.randint(*duration))
        # generate new output names and add new content (eg. key) to concatenated strings of inputs contents
        result_should_be = ''.join([f"{i.content}" for i in inputs]) + f'-{key}'
        for i, consumable_name in enumerate(self.output_consumables):
            generated = Consumable(
                consumable_name,
                result_should_be + str(i),
                self.name
            )
            self.generated_outputs.append(generated)
        print(f'Ending execution of  {self.name}')


"""Similar concern as in the Builder class. Since we're in Python and not in Java where everything
has to be a class, I'd say that `known_runners` (possibly a simple hand-written dict instead of
using `inspect` since we have only 3 runners) could be a module-level constant in
`pipeline_runners.py` and `spawn_task` could be a simple function.
Creating tasks would be a bit simpler without the need to instantiate the factory.
"""
class TaskFactory:
    """factory for runners"""

    def __init__(self):
        import MLPipeline.pipeline_runners
        self.known_runners = {}

        # scan pipeline_runners for class objects which inherit from AbstractTask and add them to the dict
        for runner_name, runner_class in inspect.getmembers(MLPipeline.pipeline_runners, inspect.isclass):
            if issubclass(runner_class, AbstractTask):
                self.known_runners[runner_name] = runner_class

    def spawn_task(self, name: str, runner: str, inputs: str, outputs: str) -> AbstractTask:
        """
        :param name: name for new runner
        :param runner_class: name of runner class
        :param inputs: list of input names
        :param outputs: list of output names
        :return: instance of runner
        """
        if runner not in self.known_runners:
            raise UnknownRunnerError(runner)
        return self.known_runners[runner](name, inputs, outputs)


class DuplicateConsumableException(Exception):

    def __init__(self, consumable: Consumable, task: AbstractTask):
        super().__init__(f"ConsumableBox with name {consumable.name} already defined on task {task.name}")


class UnknownRunnerError(Exception):

    def __init__(self, runner_name: str):
        super().__init__(f"Runner with name {runner_name} not in DB!")
