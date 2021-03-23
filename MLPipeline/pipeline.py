import datetime
import time

from MLPipeline.consumable import Consumable
from MLPipeline.pipeline_task import AbstractTask
from MLPipeline.utils import (
    is_subset_of,
    fire_and_forget
)


class DuplicateTaskException(Exception):

    def __init__(self, task: AbstractTask):
        super().__init__(f"Task with name {task.name} already defined")


class PipelineStuckError(Exception):

    def __init__(self):
        super().__init__(f"Pipeline does not converge to the desire result.")


class Pipeline:

    """You could use dataclasses to reduce these boilerplate inits. Applies to several places.
    """
    def __init__(self, name):
        self.name = name
        self.tasks_to_run = {}
        self.tasks_running = {}
        self.tasks_finished = []
        self.consumables = []
        self.expected_outputs = []

    def add_task(self, task: AbstractTask) -> None:
        """add new task to pipeline"""
        # check for duplicity
        if task.name in self.tasks_to_run:
            raise DuplicateTaskException(task)

        self.tasks_to_run[task.name] = task

    def add_input(self, input_consumable: Consumable) -> None:
        self.consumables.append(input_consumable)

    def add_output(self, output_name: str) -> None:
        self.expected_outputs.append(output_name)

    def fake_run(self) -> bool:
        # run until all expected outputs are collected
        while not is_subset_of(
                self.expected_outputs,
                [consumable.full_name for consumable in self.consumables] +
                [consumable.name for consumable in self.consumables]
        ):
            # for each task waiting in queue
            for task in self.tasks_to_run.values():
                # if task has all inputs available
                if is_subset_of(task.input_consumables, [consumable.full_name for consumable in self.consumables]):
                    # execute the task with the requested inputs
                    task_output = task.fake_execute(
                        [i for i in self.consumables if i.full_name in task.input_consumables])
                    # make the outputs available to other tasks
                    for output in task_output:
                        self.add_input(output)
                    # move task to the completed (skipping running)
                    self.tasks_finished.append(self.tasks_to_run.pop(task.name))
                    # restart the queue
                    break
            # if I have looped trough all task and not found one to run while not reaching desired output
            else:
                print(
                    [consumable.full_name for consumable in self.consumables] +
                    [consumable.name for consumable in self.consumables]
                )
                raise PipelineStuckError()

        print("Pipeline fake run converged!")
        # print("Flushing the consumables:content "
        #       "(for fake run the content is generation path output:inputs->process->output)")
        # for consumable in self.consumables:
        #     print(f"{consumable.full_name}:{consumable.content}")

        return True

    """This parallelism works but it's very fragile. You're running this method in another thread
    without any error propagations. If there is an exception, the loop in run() will run
    indefinitely since there will be some tasks in self.tasks_running. ML models are usually complex
    and a plethora of exceptions can occur, it should be somehow handled.
    """
    @fire_and_forget
    def handle_task(self, task: AbstractTask) -> None:
        """async task launcher, for simplified version look at async_pipeline_principle.py file"""
        print(f"Starting task {task.name}")
        task.execute([i for i in self.consumables if i.full_name in task.input_consumables])
        # make the outputs available to other tasks
        for output in task.generated_outputs:
            self.add_input(output)
        # move task to the completed
        self.tasks_finished.append(self.tasks_running.pop(task.name))
        print(f"Task {task.name} finished...")

    """fake_run() shares a lot of code with this method. It would be nice to deduplicate it to
    remain maintainable."""
    def run(self) -> bool:
        """async pipeline runner, for simplified version look at async_pipeline_principle.py file"""
        print("Starting async run...")
        time_start = datetime.datetime.now()
        # run until all expected outputs are collected
        while not is_subset_of(
                self.expected_outputs,
                [consumable.full_name for consumable in self.consumables] +
                [consumable.name for consumable in self.consumables]
        ):
            # for each task waiting in queue
            # you don't want to perform operations on dictionary you are iterating over :D
            task_keys = list(self.tasks_to_run.keys())
            for task_key in task_keys:
                task = self.tasks_to_run[task_key]
                # if task has all inputs available
                if is_subset_of(task.input_consumables, [consumable.full_name for consumable in self.consumables]):
                    # add task to running tasks
                    self.tasks_running[task.name] = task
                    # remove task from task que
                    self.tasks_to_run.pop(task.name)
                    # launch the task execution
                    self.handle_task(task)

            # if I have looped trough all task and didn't found one to run while not reaching desired output
            else:
                # and if no task are running ;(
                if not self.tasks_running:
                    # this should in principle happen only if you skipped the fake
                    print(
                        [consumable.full_name for consumable in self.consumables] +
                        [consumable.name for consumable in self.consumables]
                    )
                    raise PipelineStuckError()

            print(f"\nScheduler ticks... \nElapsed time {(datetime.datetime.now() - time_start).seconds} \n"
                  f"TasksToRun: {list(self.tasks_to_run.keys())} \n"
                  f"TasksRuning: {list(self.tasks_running.keys())} \n"
                  f"TasksCompleted: {[t.name for t in self.tasks_finished]} \n"
                  "\n"
                  f"Input consumables: {[c.name for c in self.consumables]}"
                  f"\nMeanwhile:"
                  )
            # tick-tock
            time.sleep(1)

        print("Pipeline run converged!")
        # print("Flushing the consumables:content "
        #       "(for real run each task type adds single letter to the string "
        #       "result is printed in format output:contents)")
        # for consumable in self.consumables:
        #     print(f"{consumable.full_name}:{consumable.content}")

        return True

    @property
    def results(self):
        """cli did not present the results in any way so I've added this property.
        """
        return {f"{consumable.full_name}": f"{consumable.content}"
                for consumable in self.consumables
                if consumable.name in self.expected_outputs}
