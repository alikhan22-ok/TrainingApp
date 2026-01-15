#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime

from engineering_team.crew import EngineeringTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

requirements = """
An app designed to create custom workout programs and track strength progress.
The app should allow users to create, name, and edit a new program, as well as edit existing programs.
The app should allow users to add and name exercises, and to remove exercises, from each program.
The app should have two dropdown menus for each exercise to select the desired rep range, one dropdown for the bottom of the rep range and another dropdown for the top of the rep range.
The app should have a minimum of one set per exercise and users should be able to add as many sets as they would like to each exercise.
The app should have a slot to type in weight and another slot to enter reps. Once the user-entered rep number hits the top of the rep range, the app automatically increases the weight by 5 lbs. """
module_name = "training.py"
class_name = "Training"


def run():
    """
    Run the research crew.
    """
    inputs = {
        'requirements': requirements,
        'module_name': module_name,
        'class_name': class_name
    }

    # Create and run the crew
    result = EngineeringTeam().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()

