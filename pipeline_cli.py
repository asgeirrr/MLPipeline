import argparse

from MLPipeline.pipeline_builder import Builder

if __name__ == '__main__':

    ap = argparse.ArgumentParser(
        usage="%(prog)s -i [INPUTS] -f [FILE] ...",
        description="""
        App take pipeline flow from .yaml file and inputs from command line.
        INPUTS should be in format a=1 b=2 (name=value separated by space).
        Next checks, if the declaration of pipeline in file is correct and all inputs are given.
        Validate if it can finish by means of fake run and finally execute live and return results."""
    )
    ap.add_argument("-i",
                    "--inputs",
                    required=True,
                    nargs='*',
                    help="list of input values in format a=1 b=2")
    ap.add_argument("-f",
                    "--file",
                    required=True,
                    help="relative path to the pipeline.yaml file")
    ap.add_argument("-b",
                    "--bad_yaml",
                    action='store_true',
                    help="If you plan to use yaml where everything is list, use this tag.")
    args = vars(ap.parse_args())

    cline_inputs = {cline_input.split('=')[0]: cline_input.split('=')[1]
                    for cline_input in args['inputs']}

    site = Builder()
    site.load_yaml(args['file'])
    site.pass_command_line_inputs(cline_inputs)
    pipe = site.build_pipeline(args['bad_yaml'])
    fake_result = pipe.fake_run()
    if fake_result:
        pipe = site.build_pipeline(args['bad_yaml'])
        pipe.run()
    print(pipe.results)
